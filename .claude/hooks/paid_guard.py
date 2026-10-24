#!/usr/bin/env python3
"""PreToolUse hook on Bash (spec 0009, AC-2): a paid run needs a human click, in every permission
mode. Anything else passes silently.

Spending has its own names, so the match is exact: a `make paid-<target>` call, or an assignment
of the env var the Python mains require before they spend (the direct `python -m` route). Plain
targets only dry-run, so nothing else can spend. A payload the hook can't read also asks: the
guard never fails open.
"""

import json
import re
import sys

PAID = re.compile(
    r"\bmake\b[^;&|\n]*\bpaid-(?:ask|eval|permissions|embed)\b|\bHANDBOOK_PAID_RUN\s*="
)
ASK = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": "paid run: needs Arun's approval",
    }
}


def main() -> int:
    try:
        command = json.load(sys.stdin)["tool_input"]["command"]
        paid = not isinstance(command, str) or bool(PAID.search(command))
    except Exception:  # unreadable payload: ask rather than let it through
        paid = True
    if paid:
        print(json.dumps(ASK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
