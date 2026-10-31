"""Spec 0012 AC-1, AC-2: the DeepInfra reranker adapter and its factory, over a fake transport."""

import json

import pytest

from handbook_rag.constants import BACKOFF_CAP, MAX_ATTEMPTS, RERANK_MODELS
from handbook_rag.models import (
    FatalRerankError,
    RerankConnectionError,
    RerankHTTPError,
    RerankResponseError,
    RerankRetriesExhausted,
    describe_reranker,
    make_reranker,
)
from handbook_rag.models.rerankers.deepinfra import DeepInfraReranker

KEY = "sk-secret-key-123"
URL = "https://example.test/rerank"


class FakePost:
    """Plays a script of bytes / exceptions, one per call; records each call."""

    def __init__(self, *script):
        self.script = list(script)
        self.calls = []

    def __call__(self, url, body, headers, timeout):
        self.calls.append((url, body, headers, timeout))
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def ok(scores, **extra):
    return json.dumps({"scores": scores, **extra}).encode()


def make(post, sleeps=None):
    sleeps = [] if sleeps is None else sleeps
    return DeepInfraReranker(
        "m/x", URL, "be relevant", KEY, 100, 8, post=post, sleep=sleeps.append, rand=lambda: 0.5
    )


def http(status, **headers):
    return RerankHTTPError(status, headers, "boom")


def test_request_url_body_headers():
    """Spec 0012 AC-1: queries repeated per document, instruction sent explicitly, bearer key."""
    post = FakePost(ok([0.1, 0.2]))
    r = make(post)
    r.rerank("q?", ["a", "b"])
    url, body, headers, _ = post.calls[0]
    assert url == URL
    assert json.loads(body) == {
        "queries": ["q?", "q?"],
        "documents": ["a", "b"],
        "instruction": "be relevant",
    }
    assert headers["Authorization"] == f"Bearer {KEY}"
    assert headers["Content-Type"] == "application/json"
    assert r.name == "deepinfra:m/x"


def test_scores_in_input_order_with_input_tokens():
    """Spec 0012 AC-1: floats in input order; the provider's input_tokens passes through."""
    result = make(FakePost(ok([3, 0.5, 2.25], input_tokens=77))).rerank("q", ["a", "b", "c"])
    assert result.scores == [3.0, 0.5, 2.25]
    assert all(isinstance(s, float) for s in result.scores)
    assert result.input_tokens == 77


def test_input_tokens_none_when_absent():
    """Spec 0012 AC-1: no input_tokens in the response gives None."""
    assert make(FakePost(ok([1.0]))).rerank("q", ["a"]).input_tokens is None


def test_empty_documents_make_no_request():
    """Spec 0012 AC-1: nothing to score, nothing sent."""
    post = FakePost()
    result = make(post).rerank("q", [])
    assert (result.scores, result.input_tokens) == ([], 0)
    assert post.calls == []


@pytest.mark.parametrize("status", [500, 503, 408, 429])
def test_transient_status_retries_then_succeeds(status):
    """Spec 0012 AC-1: 5xx, RETRY_4XX and 429 are retried with backoff."""
    sleeps = []
    post = FakePost(http(status), http(status), ok([1.0]))
    assert make(post, sleeps).rerank("q", ["a"]).scores == [1.0]
    assert len(post.calls) == 3
    assert sleeps == [0.75, 1.5]  # equal jitter at rand 0.5: 1s and 2s bases


def test_429_honours_retry_after_capped():
    """Spec 0012 AC-1: a numeric retry-after sets the sleep, capped at BACKOFF_CAP."""
    sleeps = []
    post = FakePost(http(429, **{"retry-after": "7"}), http(429, **{"retry-after": "999"}), ok([1]))
    make(post, sleeps).rerank("q", ["a"])
    assert sleeps == [7.0, BACKOFF_CAP]


def test_429_non_numeric_retry_after_uses_backoff():
    """Spec 0012 AC-1: an unusable retry-after falls back to the backoff."""
    sleeps = []
    make(FakePost(http(429, **{"retry-after": "soon"}), ok([1])), sleeps).rerank("q", ["a"])
    assert sleeps == [0.75]


def test_connection_error_retried():
    """Spec 0012 AC-1: no response (connection, timeout) is transient."""
    post = FakePost(RerankConnectionError("URLError"), ok([1.0]))
    assert make(post).rerank("q", ["a"]).scores == [1.0]
    assert len(post.calls) == 2


@pytest.mark.parametrize("status", [401, 403, 404])
def test_auth_and_not_found_are_fatal_without_retry(status):
    """Spec 0012 AC-1: retrying can't fix these."""
    post = FakePost(http(status))
    with pytest.raises(FatalRerankError):
        make(post).rerank("q", ["a"])
    assert len(post.calls) == 1


def test_other_4xx_raised_immediately():
    """Spec 0012 AC-1: a 400 is the request's fault; raised as-is, no retry."""
    post = FakePost(http(400))
    with pytest.raises(RerankHTTPError) as e:
        make(post).rerank("q", ["a"])
    assert e.value.status == 400
    assert len(post.calls) == 1


def test_exhaustion_after_max_attempts_chains_last_error():
    """Spec 0012 AC-1: a final failure raises; it never returns a fallback order."""
    sleeps = []
    post = FakePost(*[http(503) for _ in range(MAX_ATTEMPTS)])
    with pytest.raises(RerankRetriesExhausted) as e:
        make(post, sleeps).rerank("q", ["a"])
    assert len(post.calls) == MAX_ATTEMPTS
    assert len(sleeps) == MAX_ATTEMPTS - 1
    assert isinstance(e.value.__cause__, RerankHTTPError)


@pytest.mark.parametrize(
    "raw",
    [
        ok([1.0]),  # count mismatch (2 documents)
        json.dumps({"input_tokens": 3}).encode(),  # missing scores
        json.dumps({"scores": "x"}).encode(),  # not a list
        ok([1.0, "high"]),  # non-numeric
        ok([1.0, True]),  # bool is not a score
        ok([1.0, None]),
        b"[1, 2]",  # not an object
        b"<html>",  # not JSON
        b'{"scores": [1.0, NaN]}',  # review fix: json.loads accepts NaN and Infinity
        b'{"scores": [Infinity, 1.0]}',
    ],
)
def test_bad_response_raises_and_is_not_retried(raw):
    """Spec 0012 AC-1: a count mismatch or missing/bad score raises; no retry, no fallback."""
    post = FakePost(raw)
    with pytest.raises(RerankResponseError):
        make(post).rerank("q", ["a", "b"])
    assert len(post.calls) == 1


def test_key_absent_from_errors_and_repr():
    """Spec 0012 AC-1: the key never reaches an exception message or repr."""
    r = make(FakePost(http(401), *[http(503)] * MAX_ATTEMPTS))
    assert KEY not in repr(r)
    with pytest.raises(FatalRerankError) as e:
        r.rerank("q", ["a"])
    assert KEY not in str(e.value) and KEY not in str(e.value.__cause__)
    with pytest.raises(RerankRetriesExhausted) as e:
        r.rerank("q", ["a"])
    assert KEY not in str(e.value) and KEY not in str(e.value.__cause__)
    with pytest.raises(RerankResponseError) as e:
        make(FakePost(ok([]))).rerank("q", ["a"])
    assert KEY not in str(e.value)


def test_make_reranker_builds_from_constants(monkeypatch):
    """Spec 0012 AC-2: the adapter takes its settings from RERANK_MODELS."""
    monkeypatch.setenv("DEEPINFRA_API_KEY", KEY)
    r = make_reranker()
    spec, entry = next(iter(RERANK_MODELS.items()))
    assert r.name == spec
    assert r.max_input_tokens == entry["max_input_tokens"]
    assert r.template_tokens == entry["template_tokens"]
    assert r.endpoint == entry["endpoint"]


def test_make_reranker_unknown_spec_exits_listing_known():
    """Spec 0012 AC-2: an unknown spec names the known ones."""
    with pytest.raises(SystemExit) as e:
        make_reranker("deepinfra:nope")
    assert next(iter(RERANK_MODELS)) in str(e.value)


def test_make_reranker_missing_key_exits(monkeypatch):
    """Spec 0012 AC-1: a missing DEEPINFRA_API_KEY fails with its name."""
    monkeypatch.delenv("DEEPINFRA_API_KEY", raising=False)
    with pytest.raises(SystemExit, match="DEEPINFRA_API_KEY"):
        make_reranker()


def test_describe_reranker_reads_no_env(monkeypatch):
    """Spec 0012 AC-2: dry runs get the settings without a key or any env read."""
    monkeypatch.delenv("DEEPINFRA_API_KEY", raising=False)
    spec, entry = next(iter(RERANK_MODELS.items()))
    d = describe_reranker()
    assert d == {"model": spec, **entry}
    assert "api_key" not in d


def test_dropped_connection_mid_body_is_a_retried_connection_error(monkeypatch):
    """Spec 0012 AC-1 (review fix): an http.client.HTTPException while reading the body
    (IncompleteRead) maps to RerankConnectionError, which the retry loop retries."""
    import http.client

    from handbook_rag.models.rerankers import deepinfra

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            raise http.client.IncompleteRead(b"partial")

    monkeypatch.setattr(deepinfra.urllib.request, "urlopen", lambda *a, **k: Response())
    with pytest.raises(deepinfra.RerankConnectionError):
        deepinfra._urllib_post("https://example.invalid", b"{}", {}, 1.0)
