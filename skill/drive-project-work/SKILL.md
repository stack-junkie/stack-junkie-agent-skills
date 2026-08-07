---
name: drive-project-work
description: Keep consequential implementation work bound to one owner-visible slice and prevent scope transitions, verification sprawl, or broad completion claims without current acceptance evidence. Use when Codex is asked to implement, continue, finish, or ship multi-step project work; when Goal mode is explicitly requested for coding work; or when the user reports scope drift, over-verification, repeated false completion, or work continuing after a stop instruction.
---

# Drive One Project Slice

Deliver one checkable candidate without losing the broader objective. This skill has one job: keep implementation inside one bounded slice until its declared evidence is current.

## Treat the guard as a control, not paperwork

Use the machine-local slice guard before the first project mutation. Its state lives under the Codex state directory, outside the repository. It is disposable execution state, not a requirements authority, project ledger, or substitute for Git and live product behavior.

Read [references/slice-guard.md](references/slice-guard.md) before starting or resuming an implementation slice. Tell the user in one short commentary update when the guard becomes active or blocks work.

Do not use this skill for a read-only answer, diagnosis, audit, research task, or plan unless implementation is also authorized.

## Establish one slice

Inspect only enough live state to identify:

- the controlling owner instruction and nearest repository authority;
- one user-visible journey or operational result;
- the narrow files or directories that may change;
- one to five acceptance checks fixed before implementation;
- adjacent work that remains outside this slice;
- any check that only the owner, real hardware, private data, or an external system can perform.

Build the contract from owner statements, canonical requirements, reproduced behavior, and existing checks. Do not invent a new acceptance standard after seeing the implementation. Reject an outcome that bundles the entire project, backlog, all requirements, or several independently valuable journeys.

Start the guard from the Git worktree root with the session id injected by its lifecycle hook. The guard records tracked and non-noisy ignored state and rejects a broad outcome, more than five checks, repository-root-wide path authority, pre-existing edits inside allowed paths, or replacement of an unfinished slice.

If the user explicitly requested Goal mode, create the goal only after the guard starts and use the exact generated goal text. The goal's terminal meaning is candidate delivery. It is never owner acceptance, release qualification, or whole-project completion.

## Execute against the lease

1. Observe or reproduce the current behavior.
2. Make one bounded, reversible change inside the allowed paths.
3. Run only the declared checks through the guard so their actual exit status and worktree fingerprint are recorded.
4. For a declared visual or manual observation, inspect the real output and record a current artifact.
5. Re-read live Git state and the changed artifact before asking the guard for candidate status.

Do not start an adjacent package, documentation cleanup, acceptance bookkeeping, release work, or a broader suite because it is easier to prove. If new evidence changes the needed outcome, abort the current lease with the reason and establish a new one. Never silently widen it.

A failing representative workflow controls over a passing isolated check. Any later edit makes earlier evidence stale. Do not repeat or broaden verification without a changed claim, a reproduced failure that requires it, or explicit owner authorization.

## Use subagents narrowly

Default to no subagents.

- Use `reviewer` only for one fresh-context, read-only counterexample review when the slice has a high-impact visual, persistence, data-loss, concurrency, compatibility, or release-facing boundary.
- Give the reviewer the raw contract, actual diff, and artifacts. Do not give it the implementer's conclusion or ask it to reconstruct the entire project.
- Never launch repeated auditors or reviewer loops. One unresolved load-bearing finding blocks the candidate or returns to implementation.

Parallel implementation is outside this single-slice workflow. When the owner explicitly requests it, use the repository's disjoint-packet rules as a separate workflow instead of widening this lease.

The controller owns integration and the final claim. A reviewer is supplementary evidence, not an external acceptance authority.

## Obey owner stops literally

An explicit `stop`, `pause`, `do not continue`, or equivalent instruction is a hard latch. Return a concise status and use no more tools. Do not convert the stop into a preference questionnaire, process discussion, or permission to finish a nearby action. Resume only after an explicit `resume`, `continue`, `go ahead`, or `proceed` instruction.

## Report only the evidence level reached

Use exactly one of these status lines while a guarded slice exists:

- `Status: Active slice incomplete`
- `Status: Blocked`
- `Status: Needs owner decision`
- `Status: Paused by owner`
- `Status: Candidate ready`
- `Status: Candidate needs owner acceptance`

`Candidate ready` means the predeclared Codex-runnable checks passed and changed paths stayed inside the lease. `Candidate needs owner acceptance` means the same, with one or more explicitly listed owner-only or agent-observed checks still open. An agent-observed screenshot or manual interaction is evidence, not independent acceptance.

Never say the project, product, backlog, or all requested work is complete because one slice passed. Never say release-ready or owner-accepted without the separate external evidence that establishes that claim. State what changed, the exact checks and observations performed, failures, skipped gates, and the broader work still open.
