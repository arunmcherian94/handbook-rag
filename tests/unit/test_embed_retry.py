import hashlib
import logging
import math
import uuid

import pytest
from fakes import FakeEmbedder, status_error, timeout_error

from handbook_rag import embed
from handbook_rag.constants import MAX_REQUEST_TOKENS
from handbook_rag.embed import (
    FatalEmbedError,
    Pending,
    RetriesExhausted,
    Summary,
    embed_batch,
    embed_text,
    embed_with_retry,
)


def rand():
    return 0.5


def item(text, tokens=10):
    return Pending(uuid.uuid4(), uuid.uuid4(), text, tokens)


def test_retry_after_header_is_honoured():
    """AC-3: 429 with retry-after sleeps that long, then succeeds."""
    e = FakeEmbedder(errors=[status_error(429, {"retry-after": "2"})] * 2)
    sleeps = []
    out = embed_with_retry(e, ["a"], sleeps.append, rand)
    assert len(e.calls) == 3 and len(out) == 1
    assert sleeps == [2.0, 2.0]


@pytest.mark.parametrize(
    "make", [lambda: status_error(429), lambda: status_error(503), timeout_error]
)
def test_equal_jitter_backoff(make):
    """AC-3: no header -> exponential backoff with equal jitter, capped."""
    e = FakeEmbedder(errors=[make() for _ in range(5)])
    sleeps = []
    embed_with_retry(e, ["a"], sleeps.append, rand)
    assert sleeps == [0.75, 1.5, 3.0, 6.0, 12.0]
    for r, expect in ((0.0, lambda d: d / 2), (1.0, lambda d: d)):
        out = []
        embed_with_retry(
            FakeEmbedder(errors=[make() for _ in range(5)]), ["a"], out.append, lambda r=r: r
        )
        assert out == [expect(min(60, 2**n)) for n in range(5)]


def test_exhausted_after_six_attempts(caplog):
    """AC-3: 6 attempts, 5 sleeps, then RetriesExhausted and an ERROR log."""
    e = FakeEmbedder(errors=[status_error(503) for _ in range(10)])
    sleeps = []
    with caplog.at_level(logging.ERROR), pytest.raises(RetriesExhausted):
        embed_with_retry(e, ["a"], sleeps.append, rand)
    assert len(e.calls) == 6 and len(sleeps) == 5
    errs = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert errs and "InternalServerError" in errs[0].getMessage() and "6" in errs[0].getMessage()


@pytest.mark.parametrize("status", [401, 403, 404])
def test_fatal_statuses_raise_immediately(status):
    """AC-3: 401/403/404 are not retried."""
    e = FakeEmbedder(errors=[status_error(status)])
    sleeps = []
    with pytest.raises(FatalEmbedError):
        embed_with_retry(e, ["a"], sleeps.append, rand)
    assert len(e.calls) == 1 and sleeps == []


def test_poison_chunk_isolated(caplog):
    """AC-3: one bad input fails alone; the other 127 are delivered; ERROR names the chunk."""
    items = [item(f"text {i}") for i in range(128)]
    items[37].content = "has POISON inside"
    e = FakeEmbedder(poison="POISON")
    got = []
    with caplog.at_level(logging.ERROR):
        failures = embed_batch(e, items, lambda s: None, rand, lambda its, v: got.extend(its))
    assert len(got) == 127 and items[37] not in got
    assert [(f[0], f[2]) for f in failures] == [(items[37].chunk_id, 400)]
    assert any(str(items[37].chunk_id) in r.getMessage() for r in caplog.records)
    assert len(e.calls) <= 2 * math.log2(128) + 1


def test_local_validation_sends_nothing_invalid():
    """AC-3: empty or oversized chunks fail locally without a request."""
    blank, huge, good = item("  \n"), item("big", tokens=9000), item("ok")
    e = FakeEmbedder()
    got = []
    failures = embed_batch(e, [blank, huge, good], lambda s: None, rand, lambda i, v: got.extend(i))
    assert [f[2] for f in failures] == ["local", "local"]
    assert {f[0] for f in failures} == {blank.chunk_id, huge.chunk_id}
    assert got == [good]
    assert all(t == ["ok"] for t in e.calls)


def test_request_token_budget_splits_first():
    """AC-3: a batch over 300k summed tokens is split before any call."""
    items = [item(f"t{i}", tokens=8000) for i in range(50)]  # 400k > 300k
    e = FakeEmbedder()
    got = []
    failures = embed_batch(e, items, lambda s: None, rand, lambda i, v: got.extend(i))
    tokens = {i.content: i.token_count for i in items}
    assert all(sum(tokens[t] for t in call) <= MAX_REQUEST_TOKENS for call in e.calls)
    assert len(got) == 50 and failures == []
    assert len(e.calls) >= 2


def test_summary_ok():
    """AC-3: Summary.ok is false when any chunk failed."""
    assert Summary().ok
    assert not Summary(failed=[("c", "d", 400, "x")]).ok


@pytest.mark.parametrize("status", [408, 409])
def test_transient_4xx_retried(status):
    """AC-3: 408/409 are transient: retried with backoff, then succeed."""
    e = FakeEmbedder(errors=[status_error(status)])
    sleeps = []
    assert len(embed_with_retry(e, ["a"], sleeps.append, rand)) == 1
    assert len(e.calls) == 2 and sleeps == [0.75]


def test_other_4xx_isolated_like_bad_input():
    """AC-3: an unlisted 4xx (413) on a batch is split; a lone item fails with its status."""
    items = [item(f"text {i}") for i in range(4)]
    got = []
    e = FakeEmbedder(errors=[status_error(413)])
    assert embed_batch(e, items, lambda s: None, rand, lambda its, v: got.extend(its)) == []
    assert got == items and len(e.calls) == 3  # whole batch, then each half
    lone = item("x")
    failures = embed_batch(FakeEmbedder(errors=[status_error(413)]), [lone], None, rand, None)
    assert [(f[0], f[2]) for f in failures] == [(lone.chunk_id, 413)]


def test_main_without_confirm_never_embeds(monkeypatch, capsys):
    """AC-13: no --confirm -> prints the estimate and a dry-run notice; the API is never called."""

    class Boom(FakeEmbedder):
        def embed(self, texts):
            raise AssertionError("embed called on a dry run")

    class Conn:
        def execute(self, sql, params):
            assert params == ("fake:embed-test", "structural-v1", None)
            return self

        def fetchone(self):
            return (3, 1500)

        def commit(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(embed, "make_embedder", lambda: Boom(name="fake:embed-test"))
    monkeypatch.setattr(embed, "connect", lambda: Conn())
    monkeypatch.setattr(embed, "run", lambda *a, **k: pytest.fail("run called on a dry run"))
    assert embed.main(["--config", "structural-v1"]) == 0
    out = capsys.readouterr().out
    assert "embed structural-v1: 3 pending chunks for fake:embed-test, ~1500 tokens" in out
    assert "$0.0000" in out and "Dry run: add CONFIRM=1 to spend." in out


def test_unknown_config_lists_known_ids():
    """AC-4: an unknown --config exits and names the known ids."""
    with pytest.raises(SystemExit, match="fixed-512-64.*structural-v1"):
        embed.main(["--config", "nope"])


@pytest.mark.parametrize(
    "path, want",
    [
        (["A", "B"], "T\nA > B\n\nbody"),
        ([], "T\n\nbody"),
        (None, "T\n\nbody"),
    ],
)
def test_embed_text_title_path(path, want):
    """spec 0006 AC-5: title, path line (omitted when empty), blank line, content."""
    assert embed_text("T", path, "body", "title-path") == want


def test_embed_text_no_prefix_passthrough_and_unknown():
    """spec 0006 AC-5: no prefix leaves content alone; an unknown prefix is an error."""
    assert embed_text("T", ["A"], "body", None) == "body"
    with pytest.raises(ValueError):
        embed_text("T", ["A"], "body", "nope")


def test_embed_sends_prefixed_text_but_guard_is_on_content():
    """spec 0006 AC-5: the model gets the prefixed text; on_success items keep content for md5."""
    it = item("body")
    it.text = embed_text("T", ["A"], "body", "title-path")
    e = FakeEmbedder()
    got = []
    embed_batch(e, [it], lambda s: None, rand, lambda items, vecs: got.extend(items))
    assert e.calls == [["T\nA\n\nbody"]]
    assert [embed._md5(i.content) for i in got] == [hashlib.md5(b"body").hexdigest()]


def test_prefix_tokens_count_toward_limits():
    """spec 0006 AC-5: token_count + prefix_tokens is what the input and request limits see."""
    big = item("x", tokens=embed.MAX_INPUT_TOKENS)
    big.prefix_tokens = 1
    e = FakeEmbedder()
    assert len(embed_batch(e, [big], lambda s: None, rand, lambda *a: None)) == 1
    assert e.calls == []
    items = [item(f"t{n}", tokens=8100) for n in range(37)]  # 299_700: under the request cap
    e = FakeEmbedder()
    embed_batch(e, items, lambda s: None, rand, lambda *a: None)
    assert len(e.calls) == 1
    for it in items:
        it.prefix_tokens = 50  # 301_550: over it, so the request splits
    e = FakeEmbedder()
    embed_batch(e, items, lambda s: None, rand, lambda *a: None)
    assert len(e.calls) > 1
