import math
import re
from pathlib import Path

import pytest

from handbook_rag.evaluation.metrics import row_metrics
from handbook_rag.evaluation.report import is_binary, render_compare, render_md, summarize

META = {"eval_set": "v1.2", "k": 5, "mode": "full"}
NOTES = {"answer_only_facts": ["row 5 F2"], "evidence_warnings": ["row 23 F3 (optional): x"]}
CHECKS_OK = {"has_citation": True, "citations_in_range": True, "headings_exist": True,
             "no_url": True, "truncated": False, "missing_headings": []}  # fmt: skip


def abst(passed=None, false_abstention=None, label=None, abstained=False):
    return {"abstained": abstained, "passed": passed, "false_abstention": false_abstention,
            "label": label}  # fmt: skip


def records():
    return [
        {"row": 1, "type": "lookup", "recency_basis": None, "answerable": True,
         "conflict_unscored": False, "page_hit_no_chunk": False,
         "metrics": {"chunk_hit@1": 1.0, "retrieved_tokens@5": 2000.0},
         "answer": "A [1].", "truncated": False, "abstention": abst(false_abstention=False),
         "checks": CHECKS_OK},
        {"row": 2, "type": "lookup", "recency_basis": "in-page", "answerable": True,
         "conflict_unscored": True, "page_hit_no_chunk": True,
         "metrics": {"chunk_hit@1": 0.0, "retrieved_tokens@5": 2500.0},
         "answer": "B", "truncated": True, "abstention": abst(false_abstention=False),
         "checks": {**CHECKS_OK, "has_citation": False}},
        {"row": 3, "type": "recency", "recency_basis": "in-page", "answerable": True,
         "conflict_unscored": False, "page_hit_no_chunk": False,
         "metrics": {"chunk_hit@1": 1.0, "retrieved_tokens@5": 1500.0},
         "answer": "I couldn't find that.", "truncated": False,
         "abstention": abst(false_abstention=True, abstained=True), "checks": None},
        {"row": 4, "type": "ooc-off-topic", "recency_basis": None, "answerable": False,
         "conflict_unscored": False, "page_hit_no_chunk": False, "metrics": {},
         "answer": "Out of scope. Also...", "truncated": False,
         "abstention": abst(passed=False, label="abstain+extra"), "checks": None},
    ]  # fmt: skip


def test_overall_metric_exact():
    """AC-7: each metric gets mean, SE and n over the rows that have it (answerable)."""
    g = summarize(records(), META, NOTES)["groups"]["overall"]
    hit = g["chunk_hit@1"]
    assert hit["n"] == 3
    assert hit["mean"] == pytest.approx(2 / 3)
    assert hit["se"] == pytest.approx(math.sqrt((2 / 3) * (1 / 3) / 3))
    assert g["retrieved_tokens@5"]["mean"] == pytest.approx(2000.0)
    assert g["retrieved_tokens@5"]["se"] == pytest.approx(500 / math.sqrt(3))


@pytest.mark.parametrize(
    "name",
    ["chunk_hit@1", "page_hit@5", "chunk_all_required@3", "ooc_pass", "false_abstention",
     "code_checks_passed", "has_citation", "citations_in_range", "headings_exist", "no_url",
     "truncated"],
)  # fmt: skip
def test_binary_metrics(name):
    """AC-7: 0/1 metrics are classified binary by name."""
    assert is_binary(name) is True


@pytest.mark.parametrize(
    "name",
    ["chunk_fact_recall@5", "page_fact_recall@1", "chunk_mrr", "page_mrr", "chunk_ndcg@5",
     "page_ndcg@5", "retrieved_tokens@3"],
)  # fmt: skip
def test_continuous_metrics(name):
    """AC-7: continuous metrics are classified by name."""
    assert is_binary(name) is False


def test_unclassified_metric_fails_loudly():
    """AC-7: a new metric must be classified before it can be summarised."""
    with pytest.raises(KeyError, match="chunk_precision@5"):
        is_binary("chunk_precision@5")
    recs = [{**records()[0], "metrics": {"chunk_precision@5": 1.0}}]
    with pytest.raises(KeyError):
        summarize(recs, META, NOTES)


@pytest.mark.parametrize(
    "name",
    ["chunk_page_mrr", "page_chunk_hit@5", "page_all_required@5", "chunk_hit", "chunk_hit@",
     "chunk_mrr@5", "chunk_hit@5x", "xchunk_hit@5", "retrieved_tokens", "page_ooc_pass",
     "ooc_pass@5"],
)  # fmt: skip
def test_misnamed_metric_is_not_classified(name):
    """AC-7: classification is by exact name; near-misses raise instead of being guessed."""
    with pytest.raises(KeyError, match=name):
        is_binary(name)


def test_every_emitted_metric_is_classified():
    """AC-3, AC-7: every row_metrics key and every answer rate summarize emits is classified.

    Guards the paid run: a new metric that isn't classified fails here, not in summarize().
    """
    keys = row_metrics(
        chunk_facts=[{"f1"}, set()],
        pages=["a", "b"],
        required={"f1": {"a"}},
        expected_docs={"a"},
        n_relevant_chunks=1,
        token_counts=[10, 20],
    )
    for name in keys:
        is_binary(name)
    rates = set(summarize(records(), META, NOTES)["groups"]["overall"]) - {"labels"} - set(keys)
    assert rates == {"ooc_pass", "false_abstention", "code_checks_passed", "has_citation",
                     "citations_in_range", "headings_exist", "no_url", "truncated"}  # fmt: skip
    for name in rates:
        assert is_binary(name) is True


def test_continuous_metric_with_0_1_values_uses_sample_sd():
    """AC-7: fact recall that happens to be all 0/1 still gets sample sd / sqrt(n)."""
    recs = [
        {**r, "metrics": {"chunk_fact_recall@5": v}}
        for r, v in zip(records()[:3], (1.0, 0.0, 1.0), strict=True)
    ]
    s = summarize(recs, META, NOTES)["groups"]["overall"]["chunk_fact_recall@5"]
    sd = math.sqrt(((1 / 3) ** 2 * 2 + (2 / 3) ** 2) / 2)
    assert s["se"] == pytest.approx(sd / math.sqrt(3))


def test_answer_rates_and_labels():
    """AC-4, AC-5, AC-7: abstention, code-check and truncation rates over their rows; labels."""
    g = summarize(records(), META, NOTES)["groups"]["overall"]
    assert g["ooc_pass"] == {"mean": 0.0, "se": 0.0, "n": 1}
    assert g["false_abstention"]["mean"] == pytest.approx(1 / 3)
    assert g["false_abstention"]["n"] == 3
    assert g["code_checks_passed"]["mean"] == pytest.approx(0.5)
    assert g["code_checks_passed"]["n"] == 2
    assert g["has_citation"]["mean"] == pytest.approx(0.5)
    assert g["no_url"]["mean"] == pytest.approx(1.0)
    assert g["truncated"]["mean"] == pytest.approx(0.25)
    assert g["truncated"]["n"] == 4
    assert g["labels"] == {"abstain+extra": 1}


def test_groups_and_lists():
    """AC-7: by row type and by recency_basis (rows with one); conflict and chunking lists."""
    s = summarize(records(), META, NOTES)
    assert s["meta"] == META
    assert s["notes"] == NOTES
    by_type = s["groups"]["by_type"]
    assert list(by_type) == ["lookup", "ooc-off-topic", "recency"]
    assert by_type["lookup"]["chunk_hit@1"]["mean"] == pytest.approx(0.5)
    assert "chunk_hit@1" not in by_type["ooc-off-topic"]
    assert list(s["groups"]["by_recency_basis"]) == ["in-page"]
    assert s["groups"]["by_recency_basis"]["in-page"]["chunk_hit@1"]["n"] == 2
    assert s["lists"] == {"page_hit_no_chunk": [2], "conflict_unscored": [2], "near_ties": []}


def test_retrieval_only_has_no_answer_rates():
    """AC-7, AC-8: without answers, only retrieval metrics are summarised."""
    recs = [
        {**r, "answer": None, "truncated": None, "abstention": None, "checks": None}
        for r in records()
    ]
    g = summarize(recs, META, NOTES)["groups"]["overall"]
    assert set(g) == {"chunk_hit@1", "retrieved_tokens@5"}


def test_render_md():
    """AC-7: metadata, a table per group with rates to 3 dp and tokens as integers, lists."""
    md = render_md(summarize(records(), META, NOTES))
    assert md.startswith("# Eval summary\n")
    assert "- eval_set: v1.2" in md
    assert "| metric | mean | ± SE | n |" in md
    assert "## by_type: lookup" in md
    assert "## by_recency_basis: in-page" in md
    assert "| chunk_hit@1 | 0.667 | 0.272 | 3 |" in md
    assert "| retrieved_tokens@5 | 2000 | 289 | 3 |" in md
    assert "Abstention labels: abstain+extra 1" in md
    assert "- page_hit_no_chunk: 2" in md
    assert "- conflict_unscored: 2" in md
    assert "- row 23 F3 (optional): x" in md


def test_every_metric_is_defined_in_metrics_md():
    """AC-7: docs/eval/results/metrics.md defines every reported metric, and no entry is stale."""
    summary = summarize(records(), META, NOTES)
    keys = row_metrics(
        chunk_facts=[{"f1"}, set()],
        pages=["a", "b"],
        required={"f1": {"a"}},
        expected_docs={"a"},
        n_relevant_chunks=1,
        token_counts=[10, 20],
    )
    names = set(keys) | set(summary["groups"]["overall"]) - {"labels"}
    text = (Path(__file__).parents[2] / "docs/eval/results/metrics.md").read_text()
    defined = set(re.findall(r"^- `([a-z_]+(?:@k)?)`:", text, re.M))
    assert {re.sub(r"@\d+$", "@k", n) for n in names} == defined


def test_render_md_links_metrics_and_leaves_takeaways_to_fill():
    """AC-7: takeaways placeholder first, then metadata and a link to the shared definitions."""
    md = render_md(summarize(records(), META, NOTES))
    assert md.index("## Takeaways") < md.index("## Run") < md.index("## overall")
    assert "Metric definitions: [../metrics.md](../metrics.md)" in md


def _rec(row, type_, recall, hit, retrieved):
    return {"row": row, "type": type_, "metrics": {"chunk_fact_recall@5": recall,
            "chunk_hit@5": hit, "page_hit@5": 1.0, "retrieved_tokens@5": 2000.0},
            "retrieved": retrieved}  # fmt: skip


def _hit(rank, facts, heading, heading_path=None):
    h = {"rank": rank, "facts": facts, "heading": heading}
    if heading_path is not None:
        h["heading_path"] = heading_path
    return h


def test_render_compare():
    """AC-14: overall deltas, "—" for a missing side, synthesis rows added, best chunk uses
    heading_path and falls back to heading."""
    base = [_rec(1, "lookup", 0.5, 0.0, [_hit(1, [], "X"), _hit(2, ["F1"], "Old head")])]
    new = [
        _rec(1, "lookup", 1.0, 1.0, [_hit(1, ["F1"], "Old head", ["A", "B"])]),
        _rec(9, "synthesis", 0.25, 1.0, []),
    ]
    base_sum = summarize(base, META, NOTES)
    new_sum = summarize(new, META, NOTES)
    base_sum["groups"]["overall"].pop("page_hit@5")
    md = render_compare(new_sum, new, base_sum, base, "BASE-ID", [1, 77])
    assert md.startswith("## Comparison with baseline BASE-ID")
    lines = md.splitlines()
    metric_rows = [ln.split(" | ")[0].removeprefix("| ") for ln in lines[4:10]]
    assert metric_rows[:2] == ["chunk_fact_recall@5", "retrieved_tokens@5"]
    assert "| chunk_fact_recall@5 | 0.500 ± 0.000 (1) | 0.625 ± 0.375 (2) | +0.125 |" in md
    assert "| retrieved_tokens@5 | 2000 ± 0 (1) | 2000 ± 0 (2) | +0 |" in md
    assert "| page_hit@5 | — | 1.000 ± 0.000 (2) | — |" in md
    assert "| 1 | best relevant chunk | 2 · Old head | 1 · A > B |" in md
    assert "| 9 | chunk_fact_recall@5 | — | 0.250 |" in md
    assert "| 9 | best relevant chunk | — | — |" in md
    assert "| 77 | chunk_hit@5 | — | — |" in md
    assert md.index("| 77 |") < md.index("| 9 |")


def _deep(tokens, facts, pages):
    return [{"rank": i, "chunk_id": f"c{i}", "tokens": t, "facts": f, "page_relevant": p}
            for i, (t, f, p) in enumerate(zip(tokens, facts, pages, strict=True), 1)]  # fmt: skip


def _deep_rec(row, near_tie=False, **kw):
    rec = _rec(row, "lookup", 0.5, 1.0, [_hit(1, ["F1"], "H")])
    deep = _deep([100] * 6, [[], ["F1"], [], [], [], ["F2"]], [False, True] + [False] * 4)
    rec.update(deep=deep, retrieved=deep[:5], required_facts=["F1", "F2"], near_tie=near_tie)
    return rec


def test_summarize_near_ties_and_matched():
    """AC-6, AC-7: near_ties list; matched block at the k closest to the target."""
    recs = [_deep_rec(1, near_tie=True), _deep_rec(2)]
    s = summarize(recs, META, NOTES, target_tokens=210)
    assert s["lists"]["near_ties"] == [1]
    m = s["matched"]
    assert m["k"] == 2 and m["target_tokens"] == 210
    assert m["tokens"]["mean"] == 200 and m["chunk_fact_recall"]["mean"] == 0.5
    assert m["chunk_hit"]["mean"] == 1.0 and m["page_hit"]["mean"] == 1.0
    assert m["chunk_fact_recall"]["n"] == 2
    assert summarize(recs, META, NOTES, target_tokens=580)["matched"]["chunk_fact_recall"][
        "mean"] == 1.0  # fmt: skip
    assert "near_ties: 1" in render_md(s)
    assert "Token-matched k = 2" in render_md(s)


def test_matched_at_k_up_to_5_reads_the_list_the_model_saw():
    """AC-6, AC-7: on a near-tie row, matched k <= 5 scores `retrieved`, as every @5 metric
    does; k > 5 scores the deep list."""
    rec = _deep_rec(1, near_tie=True)
    rec["retrieved"] = _deep([100] * 5, [["F1"], ["F2"], [], [], []], [True] + [False] * 4)
    assert summarize([rec], META, NOTES, target_tokens=210)["matched"]["chunk_fact_recall"][
        "mean"] == 1.0  # fmt: skip
    assert summarize([rec], META, NOTES, target_tokens=600)["matched"]["chunk_fact_recall"][
        "mean"] == 1.0  # fmt: skip


def test_unscored_and_deepless_records_are_skipped():
    """AC-7: empty required_facts / missing deep -> no crash, no matched block."""
    old = [_rec(1, "lookup", 0.5, 1.0, [])]
    assert "matched" not in summarize(old, META, NOTES, target_tokens=2000)
    unscored = _deep_rec(1)
    unscored["required_facts"] = []
    assert "matched" not in summarize([unscored], META, NOTES, target_tokens=200)
    assert "near_ties: none" in render_md(summarize(old, META, NOTES))


def test_render_compare_matched_block_and_row():
    """AC-7: matched block (baseline k=5 vs this run at matched k) and per-row matched recall."""
    base = [_rec(1, "lookup", 0.5, 1.0, [])]
    new = [_deep_rec(1)]
    base_sum = summarize(base, META, NOTES)
    new_sum = summarize(new, META, NOTES, target_tokens=200)
    md = render_compare(new_sum, new, base_sum, base, "B", [1, 2])
    assert "Token-matched k (baseline k=5, this run k=2)" in md
    assert "| chunk_fact_recall | 0.500 ± 0.000 (1) | 0.500 ± 0.000 (1) | +0.000 |" in md
    assert "| tokens | 2000 ± 0 (1) | 200 ± 0 (1) | -1800 |" in md
    assert "| 1 | chunk_fact_recall@matched | 0.500 | 0.500 |" in md
    assert "| 2 | chunk_fact_recall@matched | — | — |" in md
    old = render_compare(summarize(base, META, NOTES), base, base_sum, base, "B", [1])
    assert "Token-matched" not in old and "@matched" not in old
