"""Eval harness: retrieval metrics and code checks over the eval set (spec 0004).

Functional core, imperative shell: evalset, metrics, checks and report are pure; evidence reads
the corpus and the chunks table; run is the CLI that embeds, answers and writes the run folder.
"""

from handbook_rag.evaluation.evalset import EvalSet, EvalSetError, Fact, Row, parse

__all__ = ["EvalSet", "EvalSetError", "Fact", "Row", "parse"]
