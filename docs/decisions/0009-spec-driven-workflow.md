# 0009. Spec-driven workflow with a review gate

- **Status:** accepted
- **Date:** 2026-10-07
- **Journal:** [2026-10-07 corpus and ingestion](../journal/2026-10-07-corpus-and-ingestion.md)

## Context
Work needs a review gate before any build starts.

## Decision
Adopted spec-driven flow: `specs/NNNN-*.md` → PR review and merge → plan mode builds from the spec → tests cite AC IDs → `/code-review` → diff review → clean-room.

## Consequences
Custom review agents (spec conformance, architect) are deferred.
