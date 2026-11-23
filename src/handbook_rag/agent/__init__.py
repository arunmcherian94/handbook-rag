"""Hand-rolled, multi-turn agent over the handbook (spec 0013).

- tool.py: the one tool, retrieve(query, page), with per-turn excerpt numbering
- store.py: session state in Postgres (version check + lease)
- loop.py: the tool loop, budgets, terminal states, follow-up replay, final-answer checks
- __main__.py: the CLI (`make agent` dry run, `make paid-agent` spends)

No framework: direct Chat Completions calls through the ChatModel port, so every prompt and
response is in the turn record.
"""
