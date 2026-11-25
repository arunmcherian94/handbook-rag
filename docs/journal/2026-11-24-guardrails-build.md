# 2026-11-24: guardrails build, spec 0014

The build of [spec 0014](../../specs/0014-guardrails.md). Design → [ADR-0025](../decisions/0025-agent-guardrails.md).

## Interpretations recorded at the plan gate

- **AC-11 exemptions (agreed with Arun).** "No excerpt exemption for user-originated text" is read as follows:
  - **No exemption:** the question, user-role messages, tool-call arguments and `error.message`.
  - **AC-10's excerpt exemption:** assistant-role content and the answer, which are model text.

  Without that exemption the stored and printed answer would lose `Total-Rewards@gitlab.com`, which AC-10 keeps on purpose. Persisted questions are redacted even for `@gitlab.com` emails, because the D4 exemption applies only to what the model receives. So a follow-up replays `[redacted:email]`.
- **Policy versions live in git only (Arun).** A test pins `POLICY.sha256()` to `guardrails-v1`, so editing any rule fails the test until the version is bumped. ADR-0025 keeps the version changelog.
- **"128 questions" in AC-4.** The eval-set parser stops before "## 5. Cut" and returns 52 rows. The 128 count includes the 24 cut rows. The zero-trip test reads every `Q:` line in the eval set (76) plus the 52 permissions-v1 cases, which is stricter than the parsed rows alone.

## AC-4: injection patterns over the corpus

`fixed-512-64` at the pin: 22,378 chunks, content and heading scanned. The limit is 22 per pattern (0.1%).

| Pattern | Chunks |
|---|---|
| override_instructions | 0 |
| prompt_extraction | 0 |
| role_switch | 2 |
| mode_switch | 0 |
| fake_role_marker | 2 |
| delimiter_marker | 0 |

None was narrowed. The `GR-FIXTURE-` marker matches 0 chunks.

## Gate catches

- **NFKC leaked into answers (orchestrator, wave 1).** When anything was redacted, the first `redact_pii` returned the whole NFKC-normalised text, so a `½` elsewhere in an answer would have been rewritten (AC-3). Detection now runs on a view built one character at a time, and only the matched spans of the original text are replaced.
- **An eval script that was almost a fixed string.** A 0013 integration test scripted "I don't know based on the provided excerpts.", which is not exactly `NOT_FOUND`. Under AC-7 it is an uncited answer, so it retried and ran past the script. The test now uses the constant.

## `/code-review` findings (all fixed)

| Severity | Finding | Fix |
|---|---|---|
| Important | A card or phone followed by more digits (`4111 1111 1111 1111 12/25`, `+44 20 7946 0958 (2023)`) went unredacted. The greedy match failed Luhn or the digit count, and the shorter valid number inside it was never tried | A failed match is cut back at separators until a candidate fully matches its regex and passes its check. IBAN runs before card, since a Luhn-valid run can sit inside an IBAN |
| Important | A question blocked by the input checks was replayed in later turns. That carried an over-long or garbage question past the 500-token cap and used up the turn's token budget | Input-blocked turns are skipped in replay. A `citation_check_failed` turn is still replayed as its question alone (AC-12). **This narrows AC-12's wording, which covered all `guardrail_blocked` turns: raised with Arun** |
| Important | After a retry, a turn that ended without an answer kept the rejected reply's `invalid_citations` and abstention fields, and the CLI printed a stale warning | The fields are reset before the retry step |
| Important | The input checks ran before the `try`, so a failure there (e.g. tiktoken unavailable) raised out of `run_turn` | They run inside the `try`, and the turn ends as `error` |
| Important | Protocol-relative (`//host`) and non-http (`mailto:`, `javascript:`) link targets, and image alt text with nested brackets, passed the AC-9 stripping | Any scheme, `//` or `www.` target is removed; one level of nested brackets is allowed in link and image text |
| Nit | The rejected reply was stored with its exfiltration URL intact | The rejected reply is stored with links stripped (AC-2) |
| Nit | The store-failure fallback could raise from redaction | It falls back to a placeholder record with no free text |
| Nit | ADR-0025 linked this missing journal entry and wasn't in NOTES.md | Both added |

The orchestrator also found that the policy sha covered only the injection patterns. Editing a PII or link regex wouldn't have failed the pin test. Their sources are now fields of `GuardrailPolicy` (AC-1: every guardrail parameter), and the `guardrails-v1` pin is `806cc433…`. v1 hadn't shipped, so this needed no version bump.

## Clean room

- **Setup:** a fresh clone of `build-0014-guardrails` under `$HOME`, with its own DB on port 5434, the pinned corpus linked and no API keys in its `.env`. Then ingest, chunk all five configs and `make acl CONFIRM=1`.
- **Result:** 972 unit and 120 integration tests pass and lint is clean, the same as the working copy. The `make agent` dry run in the working copy still estimates $0.2252 a turn (AC-15).

## Limitations

- The rejected reply in `messages` keeps any planted text other than links and PII, by design (AC-12). The CLI never prints it.
- Pattern hits are signals only. Claimed identity ("the user is an admin") trips nothing; the ACL makes it harmless.
