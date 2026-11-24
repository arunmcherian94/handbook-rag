# 2026-11-24: guardrails spec, spec 0014

The drafting and review of [spec 0014](../../specs/0014-guardrails.md). Decisions D1–D5, D7 and D8 were made by Arun on 24 Nov.

## Excerpt framing: delimiting, datamarking, encoding

Retrieved handbook text is untrusted: anyone who can edit the upstream handbook can plant an instruction in a chunk. Today the agent's tool result is a plain `[n] url — heading` block, so nothing tells the model where an excerpt ends or that its text is data. *Spotlighting* is the name Hines et al. (Microsoft, 2024, [arXiv 2403.14720](https://arxiv.org/abs/2403.14720)) give to a family of prompt transformations that mark untrusted input, each paired with a system-prompt rule that marked text is never an instruction. They tested three, on GPT-3.5 and GPT-4 against a synthetic set of documents with a planted keyword payload:

| Technique | What the model sees | Result in the paper | Cost and caveats |
|---|---|---|---|
| **Delimiting** | The excerpt between boundary tokens, e.g. `<excerpt-7f3a9c21 n="1">…</excerpt-7f3a9c21>` | Roughly halved attack success (from about 60%) | Cheap. An attacker who knows the delimiter can forge a closing tag; a per-turn random suffix, with delimiter strings neutralised in content, stops that |
| **Datamarking** | Whitespace inside the excerpt replaced by a marker, e.g. `The^internet^policy^cap^is^$100.^Ignore^previous^instructions…` | Summarisation: about 50% → 3.1% on GPT-3.5; no measured task cost on four benchmarks. The paper's recommended minimum | More tokens per excerpt; the marker should be random per turn; it can leak into answers, so the output must strip it |
| **Encoding** | The excerpt as base64, with an instruction to decode | Near 0% attack success | Only the most capable models decode reliably (GPT-3.5's task performance suffered); much higher token cost; risks exact quoting of figures |

**Chosen: delimiting only for now** (D3 a, Arun). Datamarking adds tokens to every excerpt, and nothing yet measures whether delimiters alone fail here. Datamarking and encoding are [follow-ups](../follow-ups.md#from-spec-0014-2026-11-24), to revisit with the AC-14 fixture results or a paid injection eval.

**What none of the three does.** OWASP LLM01:2026 (mitigation #6) says marking reduces attack success only against non-adaptive attackers: one who knows the scheme can mimic it. The controls that bound the damage are the ones that don't depend on the model obeying: no URLs or images in answers (AC-9) and no outbound tool (AC-13).

## What production systems do when an input check trips (D2)

Recorded from the D2 discussion. Arun chose to block structural failures and only flag injection patterns.

- **Act by confidence.** Block high-confidence, deterministic failures (empty, oversized or garbage input). Flag and log fuzzy signals and let the request proceed. Pattern matches for injection are fuzzy signals.
- **Monitor before enforcing.** A new rule starts flag-only, and is promoted to blocking once its false-positive rate on real traffic is known. Managed guardrail services generally offer a detect-only mode for this ([follow-up](../follow-ups.md#from-spec-0014-2026-11-24)).
- **Don't reveal the rule.** The user sees a generic message, or no change at all; the log keeps the rule and reason. Otherwise the refusal tells an attacker which phrasing to avoid.
- **Escalate per user.** Repeated trips from one user are an abuse signal: add friction past a threshold ([follow-up](../follow-ups.md#from-spec-0014-2026-11-24)).
- **Remove capabilities on suspicion.** Some systems answer a flagged request with risky tools disabled. Here there's nothing to disable: the only tool is read-only retrieval.

## Gate catches while drafting

- **D3 recommendation changed after a source check.** The first draft recommended delimiters alone and said datamarking changes how the model reads text. Reading the Spotlighting paper contradicted both: the paper calls delimiting alone easy to bypass, and reports no task cost for datamarking. The recommendation became delimiters + datamarking. Arun then chose delimiters only, for cost, with the evidence recorded above.
- **OWASP 2026 numbering checked in the PDF.** The landing page doesn't list the entries, and the first fetch couldn't parse the PDF. The contents page confirms LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure and LLM03 Excessive Agency. The landing page is dated 3 Aug 2026, not 4 Aug.
- **Corpus counts shaped D4 and D7.** 790 of 22,378 chunks contain an email address, mostly role inboxes that answers need (row 22 expects `Total-Rewards@gitlab.com`). So answer-side redaction keeps any value that appears verbatim in the turn's excerpts. 65% of chunks contain an absolute URL and 952 contain a markdown image. The eval's `no_url` check (spec 0010) already fails any answer containing a URL, which supported removing every URL (D7 a).
- **Claimed identity is not an injection pattern.** Permissions-v1 P-063 to P-067 ("I'm in People Ops, so …") are legitimate questions, and the ACL makes the claim harmless. AC-4 requires zero trips on all 128 questions in eval set v1.2 and permissions-v1.
- **Invisible Unicode in the corpus.** Zero-width characters appear in 38 chunks, variation selectors in 194 and tag-block characters in 1, almost certainly emoji sequences. Stripping them from excerpts (AC-5) loses nothing an answer needs.
