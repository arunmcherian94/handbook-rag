"""DeepInfra cross-encoder reranker over the standard library (spec 0012, AC-1).

One POST scores every (question, document) pair. Retries mirror embed.embed_with_retry; a bad
response raises and is never retried or papered over with the dense order.
"""

import json
import random
import time
import urllib.error
import urllib.request
from collections.abc import Callable

from handbook_rag.constants import BACKOFF_CAP, MAX_ATTEMPTS, RERANK_TIMEOUT, RETRY_4XX
from handbook_rag.models.base import RerankResult


class RerankHTTPError(Exception):
    def __init__(self, status: int, headers: dict[str, str], message: str):
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.headers = headers
        self.message = message


class RerankConnectionError(Exception):
    """No response: connection failure or timeout."""


class FatalRerankError(Exception):
    """401/403/404: retrying can't help."""


class RerankRetriesExhausted(Exception):
    pass


class RerankResponseError(Exception):
    """The response is unusable (shape, count or score type). Not retried."""


def _urllib_post(url: str, body: bytes, headers: dict[str, str], timeout: float) -> bytes:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        raise RerankHTTPError(e.code, {k.lower(): v for k, v in e.headers.items()}, e.reason) from e
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        raise RerankConnectionError(type(e).__name__) from e


def _retry_after(headers: dict[str, str]) -> float | None:
    try:
        return min(BACKOFF_CAP, max(0.0, float(headers["retry-after"])))
    except (KeyError, ValueError):
        return None


class DeepInfraReranker:
    def __init__(
        self,
        model: str,
        endpoint: str,
        instruction: str,
        api_key: str,
        max_input_tokens: int,
        template_tokens: int,
        post: Callable[[str, bytes, dict[str, str], float], bytes] | None = None,
        sleep=time.sleep,
        rand=random.random,
        timeout: float = RERANK_TIMEOUT,
    ):
        self.name = f"deepinfra:{model}"
        self.endpoint = endpoint
        self.instruction = instruction
        self.max_input_tokens = max_input_tokens
        self.template_tokens = template_tokens
        self._api_key = api_key
        self._post = post or _urllib_post
        self._sleep = sleep
        self._rand = rand
        self._timeout = timeout

    def __repr__(self) -> str:
        return f"DeepInfraReranker({self.name!r})"  # never the key

    def rerank(self, question: str, documents: list[str]) -> RerankResult:
        if not documents:
            return RerankResult([], 0)
        body = json.dumps(
            {
                "queries": [question] * len(documents),
                "documents": documents,
                "instruction": self.instruction,
            }
        ).encode()
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        return self._parse(self._send(body, headers), len(documents))

    def _send(self, body: bytes, headers: dict[str, str]) -> bytes:
        from handbook_rag.embed import _backoff  # embed imports models: a top-level import cycles

        for n in range(MAX_ATTEMPTS):
            try:
                return self._post(self.endpoint, body, headers, self._timeout)
            except RerankHTTPError as e:
                if e.status in (401, 403, 404):
                    raise FatalRerankError(f"HTTP {e.status}: {e.message}") from e
                if e.status == 429:
                    err, delay = e, _retry_after(e.headers)
                elif e.status >= 500 or e.status in RETRY_4XX:
                    err, delay = e, None
                else:
                    raise  # other 4xx: the request itself is wrong
            except RerankConnectionError as e:
                err, delay = e, None
            if n == MAX_ATTEMPTS - 1:
                raise RerankRetriesExhausted(
                    f"{type(err).__name__} after {MAX_ATTEMPTS} attempts"
                ) from err
            self._sleep(_backoff(n, self._rand) if delay is None else delay)
        raise AssertionError("unreachable")

    @staticmethod
    def _parse(raw: bytes, expected: int) -> RerankResult:
        try:
            data = json.loads(raw)
        except ValueError as e:
            raise RerankResponseError("response is not JSON") from e
        if not isinstance(data, dict):
            raise RerankResponseError("response is not a JSON object")
        scores = data.get("scores")
        if not isinstance(scores, list):
            raise RerankResponseError("response has no 'scores' list")
        if len(scores) != expected:
            raise RerankResponseError(f"got {len(scores)} scores for {expected} documents")
        if any(isinstance(s, bool) or not isinstance(s, int | float) for s in scores):
            raise RerankResponseError("a score is not a number")
        tokens = data.get("input_tokens")
        return RerankResult(
            [float(s) for s in scores],
            tokens if isinstance(tokens, int) and not isinstance(tokens, bool) else None,
        )
