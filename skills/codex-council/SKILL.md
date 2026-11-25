---
name: codex-council
description: Run independent Codex reviewers and a bounded revision loop to judge whether proposed workflows or delivered work actually fit the owner's requirements and preferences before returning them. Use for council reviews of how we work, unwanted output, or a plan or implementation. Editing the skill alone does not convene a council.
---

# Codex Council

Use three separate Codex agents and one coordinating agent to improve how we work together. The primary objective is less owner effort and less discarded work, not more autonomous activity. Each member inspects the evidence independently before seeing anyone else's conclusions. This provides separate review contexts, not diversity across model providers.

Inspired by [Theo's council skill](https://github.com/t3dotgg/tstack/blob/main/skills/council/SKILL.md) and [Stop Searching For the Perfect Model](https://www.youtube.com/watch?v=TWoS5Nmyoc8), particularly the owner-specific review criteria at 17:42-20:38. This adaptation uses Codex alone and bounds repeat reviews. It is separate from Council of Junipers and does not require its meetings, ballots, or memory system.

## Frame the review

For workflow reviews, read [Working around owner attention](references/workflow-review.md). Inspect current workflows and a bounded set of relevant examples. Do not assume every delay is caused by the owner, or that written rules describe actual behavior.

State the question, scope, constraints, and what a useful outcome would be. Name the concrete candidate being judged: a proposed workflow, revised skill, plan, or working artifact. A review should improve that candidate, not end with three disconnected lists of advice. For a workflow investigation, the coordinator first develops a source-backed proposal for the reviewers to challenge.

Carry forward existing implementation authorization. A review-only request stays read-only toward target projects; the coordinator may revise the requested proposal. A council recommendation does not grant permission to implement, publish, merge, or discard existing work.

For authorized implementation, finish known in-scope fixes and the relevant checks before requesting review. For planning, give members the alternatives and supporting evidence. Do not invent an implementation requirement for a discussion.

## Convene independent members

Use the available native Codex subagent tools. Prefer three fresh agents with `fork_turns: "none"`, each receiving the same candidate, factual brief, source-linked owner requirements and preferences, paths, scope boundaries, and applicable repository instructions. Do not tell members the verdict the coordinator wants or reveal other members' verdicts before their first assessment. Inherit the current model and effort unless the user specifies otherwise. Never substitute another provider.

Choose useful, overlapping perspectives for the task. Workflow defaults:

- **Owner attention and sequencing:** decisions, handoffs, dependencies, interruptions, and useful work that can continue while an answer waits.
- **Fit and rejection risk:** accepted examples, corrections, unsupported assumptions, and how to expose an unwanted direction before investing heavily in it.
- **Execution and overhead:** practical tool access, repeated reviews, coordination cost, and the smallest workable change.

For an explicitly requested implementation review, adapt these to correctness, user outcome, and simplicity. Do not make every small task convene a council.

These are optional attention guides, not fictional personalities or separate assignments. Every member reviews the whole candidate against the same owner-fit and readiness criteria. Any member may identify any material issue. For specialized work, adapt the perspectives to the question.

Members inspect sources and may use permitted command-line or API checks to challenge claims. Give them access to the actual candidate and supporting artifacts, not just the coordinator's summary. Coordinate any checks that could affect shared resources. They may ask the coordinator questions and inspect its answers. They do not change project files, spawn additional agents, contact external parties, or use browser/desktop control.

Ask each for findings, supporting evidence, proposed corrections, uncertainties, and two scores out of 10: readiness for the requested use, and fit with this owner's evidenced requirements and preferences. A 1 means fundamentally unsuitable; a 10 means no material reason found to reject this candidate within the reviewed scope. Owner fit is a reasoned estimate, not actual acceptance or a calibrated probability. Cite the owner evidence behind that judgment, distinguish explicit requirements from inferred preferences, and identify what is unknown. Missing material evidence must remain visible even if a score is high.

Honor a requested threshold such as `council 9.5`. Otherwise use 9/10 for both dimensions as this adaptation's provisional default, not a validated measure. Every required reviewer must meet the threshold; an average cannot conceal one member's supported objection. Do not change the target mid-run to obtain a pass or pressure a reviewer to raise a score.

If capacity is limited, run independent members sequentially without revealing earlier answers. If native delegation is unavailable, explain that a real council could not run. A single-agent review may still help, but must be labeled as such. Report failed or missing members instead of inventing their findings.

## Resolve findings

Check findings against the actual files, sources, or behavior. Combine duplicates. Accept, reject, or defer substantive recommendations with a reason. Do not require a quota of problems or manufacture disagreement. Preserve a well-supported minority objection even when two members disagree.

When a dispute could change the outcome, send the relevant claims and evidence back for a focused response. Ask what evidence resolves the dispute. Avoid rounds of debate about preference alone.

Do not change shared files while a member is reviewing them. After all affected readers finish, revise the proposal or apply only authorized, supported, in-scope fixes and exercise the changed behavior. When a supported finding keeps the candidate below the agreed bar, revise and return it to the same reviewers with the changes and relevant evidence. Retain honest before/after scores. Do not hand unfinished synthesis or routine fixes back to the owner as their next assignment.

Default to at most three complete review passes, including the first. Stop successfully when all required reviewers meet the agreed bar and material findings are resolved or explicitly justified. Stop unsuccessfully when the budget is reached, necessary evidence or authority is unavailable, or further work repeats positions without improving the candidate. Report the unmet bar and exact issue; do not silently lower the target. Follow a user-specified round budget. Do not grow scope to eliminate every hypothetical concern or keep creating fresh reviewers until someone approves.

Bring the owner a finished recommendation or authorized deliverable after this internal loop. Escalate earlier only for a genuinely missing consequential decision, authorization, evidence only they can supply, or an exhausted review boundary. Routine updates may stay concise, but must not require the owner to supervise the discussion. Respect an explicit owner request to see intermediate work or stop reviewing.

## Deliver the result

Lead with the recommendation or deliverable, whether it met the agreed bar, and the strongest unresolved concern. Include actual members, completed rounds, a compact readiness/owner-fit score table, material revisions, and verification limits. Show `no score` when none was returned; never reconstruct scores for an earlier unscored review. A missing required review is incomplete coverage. For workflows, show the resulting proposed way of working, owner effort removed, rejection risk, what still requires the owner, and a small real-work trial. Do not score a person's productivity or claim measured savings without evidence.

Keep the report in the current conversation unless the user requests another destination. Do not add logs, validators, persistent council memory, or publishing workflows merely to run a review. Do not claim runtime verification from agents reading code.
