# NNNN: Title

- Status: draft | approved | implemented
- Date:

## Problem

Why this work exists and what goes wrong without it.

## Depends on / frozen inputs

Fill this in before the ACs. List every input the ACs fix (model, config, run IDs, data versions, parameters) and any open decision that could change it. Choose one handling per row: **decide first** (settle the decision before the spec merges), **write as a rule** (the AC states how the value is chosen, not the value), or **accepted risk** (say why).

| Input it fixes | Open decision that could change it | Handling |
|---|---|---|
|  |  |  |

## Acceptance criteria

Each criterion is testable. Tests and plan steps cite them by ID.

- AC-1:
- AC-2:

## Out of scope

Things that will not be built here, even if they would help.

## Decisions

| Decision | Chosen | Rejected alternatives and why |
|---|---|---|

## Open questions

## Verification

The commands and checks that prove the ACs hold.

Before the implementation PR:

- [ ] `make test` and `make lint` pass
- [ ] `/code-review` run, findings ranked: must-fix items fixed, lower-priority items confirmed with a human
- [ ] Clean-room verified
- [ ] docs updated: journal entry, an ADR for any decision, follow-ups
