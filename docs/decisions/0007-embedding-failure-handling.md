# 0007. Layered embedding failure handling, cheapest isolation first

- **Status:** accepted
- **Date:** 2026-10-13
- **Journal:** [2026-10-13 baseline build](../journal/2026-10-13-baseline-build.md)

## Context
Embedding failures needed handling that isolates bad input at the lowest cost (PR #7 review and build plan).

## Decision
Layered, cheapest isolation first:
1. Check locally before sending: empty input, over 8,192 tokens, or a batch over 300k tokens. These cost no request.
2. 400/422: split the batch in half, recursively, so only the bad chunks fail. One bad chunk in 128 costs about 14 extra requests (≈ $0.003), against 128 for per-chunk retries.
3. 401/403/404: stop immediately. Splitting can't fix a key or model problem; it would only multiply failing calls.
4. 429: honour `Retry-After`, else exponential backoff with equal jitter.
5. 5xx/timeouts: whole-batch retry. There's no partial success to keep.
6. Cap of 6 attempts. SDK retries are off for the embedder so ours are the only, logged layer. The answerer keeps the SDK default (2), since it's a single interactive call.

Rejected: the Batch API (per-input errors natively, but asynchronous and needs polling code), a client-side token-bucket throttle (optimisation, out of scope), and a failures table (logs plus "no embedding row" already make failures visible and retryable).

## Consequences
- **Assumption confirmed: `Retry-After` is enough pacing at Build tier.** The full embed hit a 429 on most requests, but no batch needed more than one retry, so the 6-attempt cap has wide margin and a client-side throttle stays unneeded.

Links:
- [Embeddings reference](https://developers.openai.com/api/reference/resources/embeddings/methods/create)
- [Rate limits guide](https://developers.openai.com/api/docs/guides/rate-limits)
