# Reading log: week 5

Notes from reading done for handbook-rag. Each entry: link, summary,
and what it changes in this project. Newest first within each date.

---

## Guardrails (Tue 24 Nov)

### Beyond permission prompts: making Claude Code more secure and autonomous (Anthropic, Oct 2025)

[Beyond permission prompts](https://www.anthropic.com/engineering/claude-code-sandboxing), Anthropic Engineering (David Dworken, Oliver Weller-Davies), 20 Oct 2025. Read by Arun on 24 Nov.

**Summary (Claude-drafted):**
- Asking before every file change or command slows work down and causes approval fatigue: people stop reading what they approve, which makes the tool less safe, not more.
- The answer is sandboxing: fixed limits on what the agent can do, inside which it can act without asking. In internal use this cut permission prompts by 84%.
- There are two boundaries, and both are needed. Filesystem isolation: read and write only in the working directory. Network isolation: connect only to approved domains, through a proxy outside the sandbox that asks the user about new domains.
- One without the other fails. Without network isolation, a compromised agent can send out secrets such as SSH keys. Without filesystem isolation, it can escape the sandbox and reach the network.
- Enforcement is at the OS level (bubblewrap on Linux, seatbelt on macOS) and covers every subprocess. So a successful prompt injection is contained, not just discouraged.
- The same idea applies to Claude Code on the web: git credentials stay outside the sandbox, behind a proxy that checks scope and branch.

**How it applies to handbook-rag:**
- The same principle as the lethal trifecta, enforced outside the model. In handbook-rag the agent's network reach is fixed in code (the chat and embedding adapters), not chosen by the model, and it has no filesystem tool. Spec 0014 AC-13 turns that into a static test.
- The paid-call hook (spec 0009) is this project's permission prompt. It asks only on exact `paid-*` names so that prompts stay rare and get read, the same reason the article gives against approval fatigue.
- Budgets in code (spec 0013 AC-9) and the policy as a code constant (spec 0014 D8) follow the same idea: limits are set outside anything the model or user input can change.

**In one line:** contain the agent with hard filesystem and network boundaries enforced outside the model, so it can act freely inside them without a prompt for every step.

**My takeaway:**

### The lethal trifecta for AI agents (Simon Willison, Jun 2025)

[The lethal trifecta for AI agents](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/), Simon Willison, 16 Jun 2025. Read by Arun on 24 Nov.

**Summary (Claude-drafted):**
- The three legs: access to private data, exposure to untrusted content, and a way to communicate externally. An agent with all three can be tricked into reading private data and sending it to an attacker.
- LLMs follow instructions wherever they appear in their input. Everything becomes one token stream, so the model can't reliably tell the user's instructions from text an attacker planted.
- Asking the model in the prompt to ignore injected instructions gives no guarantee: models are non-deterministic and the attack phrasings are endless.
- Guardrail products that claim to catch "95% of attacks" don't solve it. In web security, 95% is a failing grade.
- Exfiltration channels are everywhere: any tool that makes an HTTP request, loading an image, or a link the user clicks.
- The only reliable defence is not to combine all three legs. Design patterns that stop untrusted input from triggering consequential actions (and DeepMind's CaMeL) help builders, but not end users who mix tools themselves.

**How it applies to handbook-rag:**
- Private data: the ACL-scoped chunks. Untrusted content: retrieved handbook text and the user's message. External communication: none today, since `TurnTool` exposes only a read-only `retrieve`.
- Spec 0014 keeps that leg cut and proves it: AC-13 (a static test that the agent has no outbound tool or network client) and D7 / AC-9 (no URLs or images in answers).
- Why D1 and D2 treat pattern detection as a signal, not the defence: the structural controls (the ACL pre-filter in SQL, the Principal bound in code, no egress) carry the load.

**In one line:** prompt injection can't be filtered out reliably, so never give one agent private data, untrusted content and a way to send data out all at once.

**My takeaway:**

### OWASP Top 10 for LLM Applications 2026 (OWASP GenAI Security Project, Aug 2026)

[OWASP Top 10 for LLM Applications 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/), OWASP GenAI Security Project, landing page dated 3 Aug 2026. For reference: the 2025 [LLM06 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) page. Read by Arun on 24 Nov. Covers LLM01, LLM02 and LLM03.

**Summary (Claude-drafted):**
- **The 2026 order:** LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure, LLM03 Excessive Agency (up from LLM06 in 2025).
- **LLM01 Prompt Injection:** no reliable prevention exists, because models don't separate instructions from data. Defence is architectural: assume the instruction boundary will be bypassed, and limit what the model can do and where its output can go. It cites the lethal trifecta as the pre-deployment check.
- **The LLM01 controls are layered.** Some lower attack success and weaken against adaptive attackers: role constraints in the system prompt, a provenance-labelled channel for external content, stripping invisible Unicode. Others limit the blast radius once an attack succeeds: least privilege, deterministic policy checks, and human confirmation for externally visible actions. The second group is what holds up.
- **LLM02 Sensitive Information Disclosure:** authorise before retrieval, inside the index query; minimise what is sent to the provider; scrub logs and traces before storage. It warns that regex alone is weak against encoded or multilingual output.
- **LLM03 Excessive Agency:** too much functionality, permissions or autonomy. Fix it with fewer and narrower tools, strict schemas, tools run in the user's context, human approval for high-impact actions, and authorisation in code rather than left to the model.
- **How the three link:** injection is the input-side compromise, and excessive agency is what gives it consequences outside the chat window.

**How it applies to handbook-rag:**
- Already built: authorise before retrieval (the spec 0007 ACL pre-filter in SQL), one narrow tool with a strict schema and no identity argument (`TurnTool`, spec 0013 AC-5), and budgets set in code only.
- Spec 0014 D3 / AC-5: the provenance-labelled excerpt channel, with invisible-character stripping (AC-3, AC-5).
- D4 / AC-10, AC-11: PII redaction before persistence and before the provider call. The regex-only caveat is recorded in D4.
- No human-approval step is needed while no tool has side effects. A write or send tool would need one. The paid-call hook is the human gate for spend today.

**In one line:** assume injection will succeed, and make it harmless by limiting what the model can see, do and send, enforced in code rather than in the prompt.

**My takeaway:**

---

## Mon 23 Nov 2026

### Building effective agents (Anthropic, Dec 2024)

[Building effective agents](https://www.anthropic.com/research/building-effective-agents). Read by Arun on 23 Nov. Notes drafted by Claude from the article; Arun edits. The page now notes that its tooling landscape has changed since 2024. The patterns are why it's here, not the tools.

**Summary.** The article separates *workflows* (LLMs and tools run through code paths fixed in advance) from *agents* (the LLM decides its own steps and tool use). The building block for both is an augmented LLM: a model with retrieval, tools and memory. The workflow patterns are prompt chaining, routing, parallelization (sectioning and voting), orchestrator-workers, and evaluator-optimizer. An agent is a loop of tool calls that gets ground truth from the environment at each step, has stopping conditions, and can pause at human checkpoints.

Takeaways:
- **Start with the simplest thing that works.** Our current `ask` (one retrieval plus one answer call) is the baseline the agent has to beat. Agents trade latency and cost for task performance, so the comparison has to show where that trade pays.
- **Workflow when the steps are predictable; agent when the number of steps can't be known in advance.** A single-fact lookup is a fixed workflow. A loop earns its place where one retrieval isn't enough: synthesis rows (chunk_all_required@5 = 0.125 at baseline, 1 of 8 rows), facts that sat at rank 6–8 in 5 of the 7 retrieval-side false abstentions, and multi-turn follow-ups.
- **Frameworks hide the prompts and responses underneath, which makes debugging harder.** Start with direct API calls. That's why [spec 0013](../../specs/0013-hand-rolled-agent.md) is hand-rolled, and it was the same choice as the Simpplr actions framework.
- **Agent errors compound.** Stopping conditions (max steps and budgets) and testing in a sandbox are required, not optional.
- **Ground truth at every step.** Tool results and our existing citation and abstention checks are the environment's signal. They set up Tuesday's retry-with-feedback, which is an evaluator-optimizer loop.
- **Tool design (the agent-computer interface) deserves as much care as prompts.** That means clear descriptions with examples and edge cases, formats close to natural text, and arguments shaped so mistakes are hard to make. For us: identity is never a tool argument, and retrieve takes only a query.
- **Three principles:** keep the design simple, make the agent's steps visible, and design the tool interface carefully.

- **Arun's takeaway (own words):** [Arun fills this in]

- **Decisions informed ([spec 0013](../../specs/0013-hand-rolled-agent.md)):** a hand-rolled loop with no framework; the single-pass `ask` as the baseline; a minimal tool set; budgets and named terminal states; the Principal bound server-side; every step logged to the session file for visibility.
