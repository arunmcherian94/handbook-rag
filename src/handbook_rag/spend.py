"""Spend log: one JSON line per confirmed paid run (spec 0009, AC-3).

Callers write it in a `finally` after the confirm gate, so a run that fails after spending is
still logged. The figure is the dry-run estimate, not the provider's bill.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from handbook_rag.constants import SPEND_LOG


def log_spend(
    target: str,
    est_usd: float,
    *,
    run_id: str | None,
    embed_model: str | None,
    answer_model: str | None,
    status: str,
    path: Path = SPEND_LOG,
) -> dict:
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "target": target,
        "run_id": run_id,
        "embed_model": embed_model,
        "answer_model": answer_model,
        "est_usd": est_usd,
        "status": status,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record
