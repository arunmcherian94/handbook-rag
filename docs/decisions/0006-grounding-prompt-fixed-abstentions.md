# 0006. Strict grounding prompt with two fixed abstention strings

- **Status:** accepted
- **Date:** 2026-10-13
- **Journal:** [2026-10-13 baseline build](../journal/2026-10-13-baseline-build.md)

## Context
**Parametric-leakage risk:** the GitLab handbook is almost certainly in every model's pretraining, so a model can answer correctly from memory when retrieval missed. That hides retrieval failures. Mitigations: strict grounding instructions, reading traces, and retrieval metrics scored separately from answers.

## Decision
**Prompt:** restricted to the GitLab handbook, with no training knowledge, web, documents or tools. Two fixed replies: "I don't know based on the provided handbook excerpts." (in scope, not found) and "Sorry, I don't know how to answer that." (out of scope). Fixed strings let code and the eval separate a retrieval miss from an out-of-scope question without an LLM judge. Tools are enforced in code: none are passed.

## Consequences
The prompt reduces parametric leakage but can't prevent it.
