#!/usr/bin/env python3
"""PreToolUse hook on Bash (spec 0009, AC-2): a paid run needs a human click, in every permission
mode. Anything else passes silently.

Spending has its own names, so the match is exact: a `paid-*` target name from the Makefile
anywhere in the command (so continuations, quoted separators and `gmake` don't hide it), or an
assignment of the env var the Python mains require before they spend (the direct `python -m`
route; any make or shell assignment operator). Plain targets only dry-run. A payload or Makefile
the hook can't read also asks: the guard never fails open.
"""

import json
import re
import sys
from pathlib import Path

MAKEFILE = Path(__file__).resolve().parents[2] / "Makefile"
PAID_ENV = re.compile(r"\bHANDBOOK_PAID_RUN\s*(?::{1,3}|[+?!])?=")
ASK = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": "paid run: needs Arun's approval",
    }
}


def paid_targets(makefile: Path = MAKEFILE) -> list[str]:
    targets = re.findall(r"^(paid-[a-z][a-z-]*):", makefile.read_text(), re.M)
    if not targets:
        raise ValueError(f"no paid-* targets in {makefile}")
    return targets


def is_paid(command: str, targets: list[str]) -> bool:
    names = "|".join(map(re.escape, targets))
    return bool(re.search(rf"(?<![\w-])(?:{names})(?![\w-])", command) or PAID_ENV.search(command))


def main() -> int:
    try:
        command = json.load(sys.stdin)["tool_input"]["command"]
        paid = not isinstance(command, str) or is_paid(command, paid_targets())
    except Exception:  # unreadable payload or Makefile: ask rather than let it through
        paid = True
    if paid:
        print(json.dumps(ASK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
