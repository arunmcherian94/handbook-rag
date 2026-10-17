# 0005. gpt-5.4-mini via Chat Completions, frozen through week 3

- **Status:** accepted
- **Date:** 2026-10-12
- **Journal:** [2026-10-12 baseline decisions](../journal/2026-10-12-baseline-decisions.md)

## Context
Answer-model cost math (about 3.1k input + 250 output tokens per question, about 3,500 calls over the project):

| Model | Per question | Per 100-question eval run | Whole project |
|---|---|---|---|
| Haiku 5.5 | $0.0004 | $0.04 | ~$1.50 |
| gpt-5.4-mini | $0.004 | $0.40 | ~$15 |
| Sonnet 5.5 | $0.009 | $0.87 | ~$30 |
| Opus 5.5 | $0.023 | $2.34 | ~$82 |

I initially left gpt-5.4-mini off the shortlist because its price was unverified. The user caught that, and the price was then verified on OpenAI's pricing page.

Answer API options (2026-10-13):

| | Responses | Chat Completions |
|---|---|---|
| Pros | OpenAI's recommended API for reasoning models. New features (tools, reasoning carried across turns) land here first. `output_text` helper. | The de facto OpenAI-compatible format (vLLM, Ollama, OpenRouter, Groq…), so a `base_url` reaches open and local models. Not stored server-side by default. Simple to fake. |
| Cons | Stores responses for 30 days by default (needs `store=false`). Few non-OpenAI servers implement it. Output is a list of items. | Weaker for reasoning models. Gets new features later. Some newest models (GPT-6 Astra, 6.1 Sol) can't call tools through it. |

## Decision
- Cost doesn't decide it. Chose gpt-5.4-mini for three reasons: a single provider with the embeddings, a Claude judge later is cross-family (no self-preference), and its strength is checked on the seed questions.
- **Answer API: Chat Completions, not Responses.** The baseline uses no reasoning (`reasoning_effort="none"`) and one turn, so Responses' advantages don't apply.
- The answer model and prompt stay frozen through week 3, so answer changes are attributable to retrieval (standing project rule).

## Consequences
A Responses adapter comes with the agent-layer spec, as one new class under AC-10.

Links:
- [OpenAI pricing](https://developers.openai.com/api/docs/pricing)
- [Chat Completions reference](https://developers.openai.com/api/reference/resources/chat)
- [Responses reference](https://developers.openai.com/api/reference/resources/responses)
- [Reasoning guide](https://developers.openai.com/api/docs/guides/reasoning)
- [gpt-5.4-mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini)
