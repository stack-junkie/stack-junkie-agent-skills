---
name: drive-project-work
description: Drive consequential project work from a user's outcome through orientation, decision extraction, planning, implementation, verification, release metadata, and an authorized Git checkpoint. Use for project or repository requests to drive, build, implement, fix, change, ship, continue, diagnose, audit, plan, release, or standardize work, and whenever the user expresses dislike, frustration, correction, or a desire to deviate from the standing project process.
---

# Drive Project Work

Own the project process after the user states the outcome. Ask the user only for decisions that require owner judgment, then continue through the applicable workflow without handing sequencing back to them.

## Core contract

- Preserve the complete product objective while advancing one coherent, verifiable slice at a time.
- Treat explicit user instructions and the nearest applicable repository authority as controlling.
- Inspect live state before relying on prior chat, memory, plans, versions, branches, or test counts.
- Preserve unrelated and unexpected work. Never stage a dirty worktree blindly.
- Prefer observable product behavior over code presence, task completion, builds, screenshots alone, or documentation claims.
- Make reversible engineering decisions autonomously. Ask about material product choices, irreversible actions, expanded authority, meaningful cost, protected Git actions, or conflicting authorities.
- Continue automatically after required decisions are resolved. Do not ask the user to choose routine sequencing or approve an unsurprising implementation plan.
- Do not silently reduce a broad objective to the current slice or expand the slice into adjacent work.

## Interpret the request

Infer the operating mode from the user's language:

- **Drive:** `drive`, `build`, `implement`, `fix`, `change`, `add`, `remove`, `ship`, or another request that clearly authorizes project changes. Investigate, implement, verify, apply release hygiene when warranted, and create only the authorized checkpoint.
- **Diagnose:** determine the cause from read-only evidence. Do not implement unless the user also asks for a fix.
- **Plan:** investigate and produce a decision-ready plan. Do not edit production files unless the user explicitly authorizes implementation.
- **Audit or review:** inspect and report evidence. Do not mutate external state or fix findings unless requested.
- **Release:** perform release-readiness and release operations only within explicit repository and owner authorization. Tagging, publishing, protected refs, signing, and distribution remain separate permissions.
- **Continuous delivery:** continue from one verified slice to the next only when the user explicitly authorizes continuous project delivery.

If the mode is genuinely ambiguous and mutation would matter, ask one concise question. Otherwise use the narrowest mode consistent with the request.

## Orient before acting

For consequential work, begin with a bounded read-only pass:

1. Confirm the exact project root and applicable instruction chain.
2. Inspect branch, worktree, staged state, remotes, and unexpected changes.
3. Locate authoritative requirements, accepted decisions, active delivery frontier, version source, changelog, build commands, and verification commands.
4. Classify the project as maintained product, planning-stage product, operational workspace, prototype or spike, or third-party/reference checkout.
5. Classify the task as investigation, planning/governance, internal-only change, shipped product change, packaging/schema/persistence change, or release operation.
6. Identify the real production flow and mutable state owner before editing.

Use `scripts/inspect_project.ps1` for the initial mechanical inventory when PowerShell is available. Treat its output as orientation, not as proof of completion. Keep searches scoped to the explicit project root.

Report orientation only when it reveals a material constraint, dirty-path concern, release consequence, or blocker.

## Extract owner decisions

Sort ambiguity into three buckets:

1. **Already answerable:** resolve from accepted decisions, current behavior, source, tests, architecture, and repository conventions. Do not ask.
2. **Safe engineering judgment:** decide autonomously when the choice is reversible, internal, and consistent with existing patterns. Record consequential reasoning when useful.
3. **Owner decision:** ask when the choice changes user-visible behavior, product scope, UX direction, compatibility, data safety, dependencies, privacy, cost, legal posture, protected Git state, publication, or required permissions.

Ask no more than three high-value questions in one round. For each, provide:

- the decision;
- why it matters now;
- two or three materially different options;
- a recommendation;
- concrete reasoning and evidence;
- what approval authorizes.

Do not ask which backlog item or implementation step to do next when project authorities already determine the order.

### Apply the 93 percent intent gate

Do not implement an affected user-visible or domain-semantic decision until confidence in the user's intent is at least 93 percent. Treat this as an evidence gate, not a claimed psychological probability.

Score these 14 intent checks as `clear` or `unclear`; 13 of 14 clear checks rounds to 93 percent:

1. intended outcome;
2. target user and use context;
3. triggering workflow or starting state;
4. current behavior being kept or changed;
5. desired visible behavior;
6. included scope;
7. excluded scope;
8. controlling reference behavior or source precedence;
9. data, signal, field, or domain meaning when applicable;
10. interaction and information structure;
11. compatibility and persistence expectations;
12. error, unavailable, empty, and partial states;
13. observable completion and acceptance criteria;
14. permission, risk, and delivery boundary.

The outcome, desired behavior, included scope, controlling reference, applicable domain meaning, and completion criteria are critical checks. Never proceed with the affected decision while a critical check is unclear, even if the numerical threshold is otherwise met. Mark a check clear only from an explicit owner statement, an accepted canonical decision, or directly observed reference behavior that the owner has authorized as controlling. Do not use an inference, a likely convention, or an agent preference as a clear check.

When below the gate, continue safe read-only discovery, state the uncertain interpretation and current score, and ask up to three questions that eliminate the most uncertainty. Include the recommended answer and reasoning, but do not let the recommendation substitute for the owner's answer. Repeat until the gate is met. Apply the gate only to the affected ambiguous decision; do not stall unrelated work whose intent is already clear.

## Detect preference and process deviations

Keep watching for feedback that may conflict with the standing process, even when the user does not phrase it as a formal rule change. Signals include:

- explicit dislike such as `I hate this`, `don't do that`, or `stop doing this`;
- frustration, surprise, or corrective language about how the work is being handled;
- repeated steering away from the same behavior;
- a request that contradicts a current default, skill rule, or repository workflow;
- praise or preference that suggests a better recurring default.

Do not silently ignore the signal, silently violate the process, or silently convert an offhand reaction into a permanent rule.

When a signal is material:

1. Pause only the affected action if continuing could compound the unwanted behavior.
2. State the current rule or default in plain language.
3. Explain how the user's request or reaction deviates from it.
4. Give a recommendation and explain the reasoning, including tradeoffs.
5. Ask whether the deviation is:
   - **This task only**: apply it only to the current task or thread.
   - **Future default**: update the maintained source skill after confirmation.
   - **Not a process change**: treat it as feedback or clarification without changing the rule.

Use wording like:

> This differs from the current process, which does X. I recommend Y because Z. Should I treat this as a one-time exception, change the default for future project work, or leave the process unchanged?

Do not overreact to harmless conversational wording. Raise the distinction when the signal could reasonably change future behavior or when repeating the current process would likely frustrate the user again.

## Update this process safely

The maintained source is:

`C:\Users\stack-junkie\Documents\Development\02 Projects\Agent Skills\drive-project-work`

The installed runtime copy under `C:\Users\stack-junkie\.codex\skills\drive-project-work` is not the source of truth.

When the user confirms a future-default change:

1. State the old rule, the new rule, and the expected behavioral effect.
2. Inspect the source repository and its `AGENTS.md` before editing.
3. Change the narrowest durable instruction or reference. Avoid adding a second competing rule.
4. Update examples or deterministic scripts only when the behavior requires it.
5. Bump the skill version and add a concise changelog entry.
6. Run the repository checks and the official skill validator.
7. Reinstall from the maintained source into the runtime skill directory.
8. Verify the installed copy matches the source.
9. Review the diff and create only the authorized Git checkpoint.
10. Report the new version, changed behavior, validation, install status, and Git status.

For a one-time exception, do not edit this skill, repository rules, global instructions, or memory. State the exception in the active thread and continue.

If the user asks to remember a preference outside this skill, follow the environment's explicit memory-update policy separately.

## Define and pursue the active goal

Do not turn a vague request directly into a long-running goal. After orientation and decision extraction, formulate the operational goal with:

- **Outcome:** the user-visible or operational result;
- **Constraints:** behavior, data, architecture, compatibility, and scope that must be preserved;
- **Verification:** tests, measurements, workflows, and review criteria that prove completion;
- **Outside this slice:** related work that remains part of the broader objective but is not being changed now.

Use Goal mode when available for multi-step implementation. Keep the same coherent chat while pursuing the goal. Continue from milestone to milestone without asking `what next?`.

Use a living execution plan only when the work must survive multiple sessions, contains significant uncertainty, or spans several independently verifiable milestones. Do not create planning artifacts for routine work.

## Execute the verified slice

1. Reproduce or observe the current behavior when practical.
2. Trace the production flow and choose the narrowest correct ownership boundary.
3. Reuse compatible behavior and existing project conventions.
4. Implement the complete interaction, including relevant error, unavailable, cancellation, recovery, persistence, packaging, and UI states.
5. Add narrow regression coverage for reproduced defects and risky boundaries.
6. Run focused checks early, then the highest applicable integrated verification.
7. Diagnose and repair ordinary failures within scope without asking the user to manage the loop.
8. Exercise the real production path with representative inputs.
9. Inspect material visual output directly when the result is visual.
10. Review the complete diff for regressions, unrelated changes, fabricated success, and missing behavior.

Read `references/verification-levels.md` when choosing or reporting the verification boundary.

## Apply release hygiene

Read `references/release-classification.md` before changing a version or changelog.

- Apply the repository's existing release convention when it is sound.
- Version coherent shipped behavior, not turns, prompts, agent activity, plans, or intermediate attempts.
- Do not bump product versions for investigation, unaccepted planning, governance-only instructions, or internal documentation unless those artifacts are distributed product behavior.
- For active alpha products, increment the prerelease sequence once per coherent shipped checkpoint unless the repository defines another rule.
- Keep implementation detail, agent process, verification transcripts, and private planning out of public changelogs.
- If a repository lacks a release process, do not invent one during an unrelated task. Report the gap and recommend a separate onboarding action.

## Checkpoint safely

Before Git mutation:

1. Inspect tracked, untracked, ignored, and staged paths.
2. Review the full intended diff.
3. Exclude unrelated user work, secrets, machine-local debris, generated noise, and proprietary data.
4. Confirm required version references and generated files are synchronized.
5. Run applicable repository, secret, and release checks.

Default behavior for a completed maintained-product change is one coherent commit and a push only to an already configured, authorized, non-protected ref. Repository-specific rules and explicit user instructions override this default.

Never infer permission to modify protected refs, tag, publish, release, alter remotes, rewrite history, force-push, or distribute artifacts.

## Apply the EtherPlot delivery cadence

For EtherPlot, treat each coherent, independently testable slice as its own published checkpoint:

1. Complete the implementation, focused checks, integrated build, and real workflow exercise.
2. For visual changes, capture representative screenshots outside the repository, inspect every
   image directly, and do not call the result good until the visible result has been reviewed.
3. Increment the configured alpha prerelease sequence, add the product changelog entry, create one
   reviewed commit, and push only to the repository-authorized checkpoint branch.
4. Immediately report the version, commit, branch, behavior delivered, exact test steps, expected
   results, and remaining caveats in the active chat.
5. Send the same test note to the owner's connected email account as a self-email. Attach or link
   inspected screenshots when the email connector supports it. If email is unavailable, report the
   failed delivery without withholding the Git checkpoint or chat instructions.

Do not accumulate several completed EtherPlot slices behind one late version bump or notification.
After implementation is otherwise complete, perform a documentation-reconciliation slice: rewrite
the README around the actual setup and user journeys, replace or remove stale documentation, keep
canonical authorities intact, and publish that documentation slice through the same cadence.

## Stop conditions

Stop and ask with evidence, options, recommendation, and exact required authority when:

- authoritative sources conflict;
- dirty-path ownership cannot be established;
- meaningful data-loss or irreversible risk appears;
- scope or permissions must materially expand;
- a new dependency, account, credential, cost, or external service is required;
- a genuine product decision remains unresolved;
- protected Git, publication, signing, or distribution authority is required;
- required verification depends on unavailable hardware, private data, accounts, or owner judgment;
- the same blocker persists and measurable progress is no longer possible;
- the user pauses or stops the work.

## Report the result

Lead with the outcome. Include only applicable sections:

- **Outcome:** what now works or what was learned.
- **Changed:** behavior-level summary.
- **Verified:** exact checks, real workflows, visible results, and failures.
- **Release metadata:** version transition and changelog status, or why not applicable.
- **Git:** commit, push, tag, and release status.
- **Remaining:** skipped, blocked, unverified, or next-frontier work.

Never describe the whole project as complete merely because the active slice succeeded.
