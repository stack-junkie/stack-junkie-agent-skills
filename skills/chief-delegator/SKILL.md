---
name: chief-delegator
description: Lead sustained product work through bounded delegation, independent review, and continuity of the full approved outcome. Use when a chief should retain integration and acceptance ownership while workers handle implementation detail.
license: MIT
---

# Chief Delegator

Keep the complete approved product outcome in view while delegating bounded detail. Compose `parallel-issue-orchestration` for lane isolation and host ownership with `preserve-compaction-continuity` for approval retrieval and recovery. Read both skills from the available skill catalog before dispatch. If either is unavailable, identify the missing guidance and continue only supported work. Using this skill does not authorize delegation, installation of hooks, publication, or broader scope by itself.

## Own the outcome

The chief owns the objective, observable acceptance coverage, priorities, dependencies, shared interfaces, integration decisions, continuity, and factual progress. Delegate source exploration, debugging, implementation, and focused verification. Keep the team shallow and adapt it to actual available slots, disjoint ownership, and host capacity. Workers do not delegate further unless explicitly assigned and authorized. Work locally when separation would add overhead without useful independent work.

Before implementation, retrieve the controlling approval, any proposal it approves, and subsequent corrections. Define observable acceptance from those requirements, including the complete user journey and relevant failure or recovery behavior. Tie each requirement to an observable result and current evidence or an explicit gap. Resolve consequential product ambiguity with the owner; routine implementation choices remain with the chief. Do not turn an internal milestone into a new finish line.

Reuse existing plans, decisions, and handoffs plus one compact active state record. Keep original approvals retrievable by exact source reference, with verbatim approved material when existing storage cannot retain it. The active record points to requirements and evidence, current acceptance gaps, lane ownership, source identities, dependencies, decisions, and next actions. Record decision rationale, supporting evidence, assumptions, rejected alternatives that matter, and conditions for reopening the decision. Preserve useful conclusions, never private chain-of-thought. Do not create another board, report hierarchy, or evidence registry.

## Dispatch bounded work

Give each worker or reviewer a self-contained brief with:

- outcome and exact authoritative requirements, with retrievable source locations;
- verified source baseline, including relevant local and untracked changes, not just a commit;
- exclusive writable paths, read-only inputs, and forbidden areas;
- dependencies, shared contracts, and chief-owned integration points;
- observable acceptance and proportionate checks;
- location for evidence and the required return;
- host limits and named ownership of scarce build, runtime, or interactive resources;
- escalation and stopping boundary, including publication permissions and what to preserve on interruption.

Supply the minimum raw context needed to judge the assignment. Request a concise return: outcome, changed paths, acceptance/check results, evidence references, material uncertainty, and next action. Keep long logs in existing artifacts and allow detail when needed to expose a problem. Do not impose a token cap that hides contrary evidence.

## Review and integrate

Assign independent reviewers bounded questions against authoritative requirements and current artifacts. Independence means they did not implement the work being judged and can reach a different conclusion. Give them raw evidence and the source identity, not a suggested verdict. Schedule review with the available slots; independence does not require concurrent execution or a fixed team size.

The chief or an explicitly assigned independent verifier inspects relevant diffs and high-impact or contradictory evidence. A worker summary alone cannot establish acceptance. Name the verifier, checks, evidence location, and resource ownership; serialize scarce resources. The chief reconciles contradictions, shared interfaces, stale checks after integration, and remaining coverage before accepting a lane. Distinguish implemented, verified, owner-accepted, and still uncertain.

When a worker is interrupted, preserve its unfinished patch and inspect live artifacts and status before resuming or reassigning ownership. Establish that the previous writer has stopped, identify partial versus usable changes, and hand off the actual baseline. Do not reset unfinished work or launch a second writer into the same paths.

## Continue toward acceptance

Choose work loops that improve an observable user or player behavior, verify a named acceptance gap, or resolve a named blocker. Update the compact state at consequential changes rather than producing process artifacts as progress. Repeated failed attempts require a revised diagnosis or changed evidence, inputs, or approach before another attempt.

When one action is blocked, continue useful independent authorized lanes. Ask the owner only for consequential scope, product, or authority decisions that cannot be resolved from existing instructions. If nothing useful can proceed, report the exact blocked action, affected acceptance, and what would unblock it. Do not invent busywork or silently lower the objective.

After compaction or handoff, use the continuity skill to retrieve the full controlling requirements and later corrections. Reconcile them with live changes, worker status, ownership, decisions, and outstanding acceptance before resuming. A recent-message window, packet header, verified hash, or predicted compaction time cannot replace that reconciliation. Keep state current through the work rather than depending on a last-minute compaction warning.

Before claiming completion, reconcile every approved requirement with current evidence for the integrated product and disclose unresolved limits. Passing tests, worker delivery, internal milestones, and completed process artifacts do not establish a complete journey. Report actual progress and the remaining boundary honestly; stop only at the approved scope boundary, fulfilled acceptance, or a blocker that leaves no useful authorized work.
