"""Deterministic, offline stand-ins for the model adapters (spec 0003, AC-9). No network.

FakeEmbedder / FakeAnswerer satisfy the Embedder / Answerer Protocols structurally (no
inheritance), so pipeline code runs on them unchanged. FakeOpenAIClient is injected into the
real adapters to test their request and response handling.
"""

import copy
import hashlib
import json
import math
import re
from types import MappingProxyType, SimpleNamespace

import httpx2
import openai

from handbook_rag.identity import Principal
from handbook_rag.models import ChatStep, Completion, RerankResult, ToolCall

_REQ = httpx2.Request("POST", "https://api.openai.com/v1/embeddings")
_STATUS_ERRORS = {
    400: openai.BadRequestError,
    401: openai.AuthenticationError,
    403: openai.PermissionDeniedError,
    404: openai.NotFoundError,
    422: openai.UnprocessableEntityError,
    429: openai.RateLimitError,
    500: openai.InternalServerError,
    503: openai.InternalServerError,
}


def status_error(status: int, headers: dict | None = None) -> openai.APIStatusError:
    """A real SDK exception for an HTTP status, as the OpenAI client would raise it."""
    resp = httpx2.Response(status, headers=headers or {}, request=_REQ)
    cls = _STATUS_ERRORS.get(status, openai.APIStatusError)
    return cls(f"fake HTTP {status}", response=resp, body=None)


def timeout_error() -> openai.APITimeoutError:
    return openai.APITimeoutError(request=_REQ)


def bow_vector(text: str, dims: int = 256) -> list[float]:
    """Hashed bag-of-words, L2-normalised: texts sharing words get a smaller cosine distance."""
    v = [0.0] * dims
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        v[int(hashlib.md5(word.encode()).hexdigest(), 16) % dims] += 1.0
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


class FakeEmbedder:
    """Embedder with scriptable failures.

    errors: exceptions raised by successive calls before calls start succeeding.
    poison: any batch containing a text with this substring raises HTTP 400 (all-or-nothing,
        like the real endpoint).
    fail_after: raise RuntimeError on the call after this many successful calls (a crash).
    """

    def __init__(
        self,
        name="fake:bow",
        dims=256,
        errors=(),
        poison=None,
        fail_after=None,
        kind="document",
        max_input_tokens=8192,
    ):
        self.name = name
        self.kind = kind
        self.max_input_tokens = max_input_tokens
        self.dims = dims
        self.errors = list(errors)
        self.poison = poison
        self.fail_after = fail_after
        self.calls: list[list[str]] = []  # every batch attempted, including failed ones
        self.successes = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        if self.errors:
            raise self.errors.pop(0)
        if self.poison is not None and any(self.poison in t for t in texts):
            raise status_error(400)
        if self.fail_after is not None and self.successes >= self.fail_after:
            raise RuntimeError("simulated crash")
        self.successes += 1
        return [bow_vector(t, self.dims) for t in texts]


class FakeAnswerer:
    def __init__(self, text="", name="fake:answer", truncated=False):
        self.text = text
        self.name = name
        self.truncated = truncated
        self.calls: list[tuple[str, str]] = []

    def answer(self, system: str, user: str) -> Completion:
        self.calls.append((system, user))
        return Completion(
            text=self.text, input_tokens=100, output_tokens=20, truncated=self.truncated
        )


class FakeOpenAIClient:
    """Records request kwargs; returns SDK-shaped responses for adapter contract tests."""

    def __init__(
        self, dims=1536, answer="ok", finish_reason="stop", reverse_order=True, tool_calls=None
    ):
        """tool_calls: (id, name, arguments) triples returned as message.tool_calls (spec 0013)."""
        self.requests: list[tuple[str, dict]] = []
        self.dims = dims
        self.answer = answer
        self.finish_reason = finish_reason
        self.tool_calls = tool_calls
        self.reverse_order = reverse_order
        self.embeddings = SimpleNamespace(create=self._embed)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._chat))

    def _embed(self, **kwargs):
        self.requests.append(("embeddings", kwargs))
        data = [
            SimpleNamespace(index=i, embedding=[float(i)] * self.dims)
            for i in range(len(kwargs["input"]))
        ]
        if self.reverse_order:  # the API documents `index`; don't rely on list order
            data.reverse()
        return SimpleNamespace(data=data, usage=SimpleNamespace(prompt_tokens=7, total_tokens=7))

    def _chat(self, **kwargs):
        self.requests.append(("chat", kwargs))
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=self.answer,
                        tool_calls=self.tool_calls
                        and [
                            SimpleNamespace(
                                id=i, type="function", function=SimpleNamespace(name=n, arguments=a)
                            )
                            for i, n, a in self.tool_calls
                        ],
                    ),
                    finish_reason=self.finish_reason,
                )
            ],
            usage=SimpleNamespace(prompt_tokens=50, completion_tokens=10),
        )


def make_principal(*groups: str, user_id: str = "test") -> Principal:
    """A Principal with exactly these groups, for tests outside src/ (spec 0007, AC-8)."""
    return Principal(user_id, MappingProxyType({}), frozenset(groups))


class FakeReranker:
    """Reranker (spec 0012) scoring each document by a callable (default: shared words with the
    question). Records every call; fail raises on every call (no fallback may hide it)."""

    name = "fake:reranker"
    max_input_tokens = 32768
    template_tokens = 80

    def __init__(self, score=None, input_tokens: int | None = 42, fail: Exception | None = None):
        self.score = score or (
            lambda q, d: len(
                set(re.findall(r"[a-z0-9]+", q.lower())) & set(re.findall(r"[a-z0-9]+", d.lower()))
            )
        )
        self.input_tokens = input_tokens
        self.fail = fail
        self.calls: list[tuple[str, list[str]]] = []

    def rerank(self, question: str, documents: list[str]):
        self.calls.append((question, list(documents)))
        if self.fail is not None:
            raise self.fail
        return RerankResult([float(self.score(question, d)) for d in documents], self.input_tokens)


def tool_step(query: str, page: int = 1, call_id: str = "call_1", **extra) -> ChatStep:
    """A scripted model step that calls retrieve once (spec 0013); extra adds arguments."""
    args = json.dumps({"query": query, "page": page, **extra})
    return ChatStep("", (ToolCall(call_id, "retrieve", args),), 100, 20, "tool_calls")


def raw_tool_step(arguments: str, name: str = "retrieve", call_id: str = "call_1") -> ChatStep:
    """A tool call with arbitrary raw arguments or tool name, for malformed-call tests."""
    return ChatStep("", (ToolCall(call_id, name, arguments),), 100, 20, "tool_calls")


def final_step(text: str, finish_reason: str = "stop", input_tokens: int = 100) -> ChatStep:
    return ChatStep(text, (), input_tokens, 20, finish_reason)


class FakeChatModel:
    """ChatModel (spec 0013, AC-1) returning scripted steps, recording every call.

    script: a list of ChatStep or Exception, consumed in order (an Exception is raised), or a
        callable (call_index, messages, tools, tool_choice) -> ChatStep for open-ended scripts.
    Running past the end of a list fails the test.
    """

    def __init__(self, script, name="fake:chat"):
        self.script = script if callable(script) else list(script)
        self.name = name
        self.calls: list[dict] = []

    def complete(self, messages, tools, tool_choice, timeout=None) -> ChatStep:
        i = len(self.calls)
        self.calls.append(
            {
                "messages": copy.deepcopy(messages),
                "tools": copy.deepcopy(tools),
                "tool_choice": tool_choice,
                "timeout": timeout,
            }
        )
        if callable(self.script):
            out = self.script(i, messages, tools, tool_choice)
        else:
            assert i < len(self.script), f"FakeChatModel: unscripted call {i + 1}"
            out = self.script[i]
        if isinstance(out, Exception):
            raise out
        return out
