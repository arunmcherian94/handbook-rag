"""Spend log: one JSON line per confirmed paid run (spec 0009, AC-3).

Callers write it in a `finally` after the confirm gate, so a run that fails after spending is
still logged. est_usd is the dry-run estimate, not the provider's bill. actual_usd, when a
runner passes it, is that runner's own tally from token counts at the price tables in code (spec
0015 AC-7); the key is left out otherwise.
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from handbook_rag.constants import SPEND_LOG

PAID_ENV = "HANDBOOK_PAID_RUN"  # set only by the `make paid-<target>` recipes


def paid(confirm: bool, target: str) -> bool:
    """Spec 0009, AC-1, AC-2: spend only with --confirm and PAID_ENV=1, so every route that spends
    goes through a name the hook matches. Prints the dry-run notice otherwise."""
    if not confirm:
        print(f"Dry run: `make paid-{target}` spends.")
        return False
    if os.environ.get(PAID_ENV) != "1":
        raise SystemExit(f"--confirm spends only via `make paid-{target}` ({PAID_ENV}=1)")
    return True


def log_spend(
    target: str,
    est_usd: float,
    *,
    run_id: str | None,
    embed_model: str | None,
    answer_model: str | None,
    status: str,
    path: Path = SPEND_LOG,
    actual_usd: float | None = None,
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
    if actual_usd is not None:
        record["actual_usd"] = actual_usd
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record
