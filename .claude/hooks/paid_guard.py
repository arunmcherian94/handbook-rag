#!/usr/bin/env python3
"""PreToolUse hook on Bash (spec 0009, AC-2): a command that spends (CONFIRM=1 or --confirm)
needs a human click, in every permission mode. Anything else passes silently."""

import json
import re
import sys

PAID = re.compile(r"\bCONFIRM=1\b|--confirm\b")


def main() -> int:
    command = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    if PAID.search(command):
        reason = "paid call (CONFIRM=1 / --confirm): needs Arun's approval in this session"
        out = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": reason,
            }
        }
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
