# Reading log: week 5

Notes from reading done for handbook-rag. Each entry: link, summary,
and what it changes in this project. Newest first within each date.

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
