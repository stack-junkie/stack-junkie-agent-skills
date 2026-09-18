---
name: parallel-issue-orchestration
description: Coordinate parallel agents early in long tasks with independent engineering lanes or GitHub issues. Use for separable investigations, implementation, or review when delegation is authorized. Avoid small or tightly coupled tasks.
license: MIT
---

# Parallel Issue Orchestration

Coordinate independent engineering lanes without letting agents collide or lose the accepted objective. A project can have useful parallel lanes without GitHub issues or even a Git repository. Use live state and file ownership to decide what can run independently.

## Select early and preserve the coordinator

At the start of sustained work, identify whether at least two concrete, bounded lanes can proceed independently while the coordinator does useful work. When delegation is authorized by the user or applicable instructions, dispatch suitable lanes before loading all their detailed tool output into the coordinator. If lanes are coupled, small, or require the same scarce resource, work locally or sequence them. Skill selection does not override higher-priority restrictions on spawning agents.

Keep the accepted objective, acceptance requirements, current user constraints, and integration decisions with the coordinator. Delegate bounded source investigation, analysis, implementation, or independent review. Do not substitute successful worker deliverables for the user's full finish line.

Delegation can reduce detailed tool output in the coordinator's context. It also adds dispatch, review, and reconciliation overhead, and does not guarantee fewer total tokens or prevent compaction. Preserve continuity independently of agent count.

Reassess after the initial investigation or a scope change exposes new independent work. Do not defer all delegation until context pressure appears. State the selected lanes briefly, or the concrete coupling or authorization restriction that requires local work, without creating a separate assessment document.

## Preserve scope and authorization

Resolve consequential ambiguity about expected behavior, scope, and ownership before dispatching workers. Ask focused questions only when the answer changes implementation, sequencing, or external actions. Recheck the boundary when scope expands, collaborator ownership is uncertain, or direct evidence does not support closure.

Authorization to investigate or implement does not automatically authorize commits, pushes, issue comments, pull requests, merges, releases, issue closure, or deletion of branches and worktrees. Establish the authorized stopping point before dispatch and preserve it in every worker prompt.

A live-state check detects staleness and conflicts. It does not expand the owner's scope. When the owner names a bounded issue set, inspect those issues and only the related issues, pull requests, branches, and handoffs needed to detect overlap. Inventory every open issue only for a repository-wide pass. Report relevant omitted or newly opened issues without adding them to the work unless authorized.

## Establish a safe baseline

1. Read project instructions, the accepted plan, and current implementation evidence. Distinguish authoritative user requirements from historical progress summaries.
2. Inspect active processes and existing artifacts relevant to the work. For Git repositories, inspect status, branch, remotes, recent history, and registered worktrees.
3. For Git worktrees, record the verified base branch and commit SHA plus the relevant dirty-source identity: source checkout, changed and untracked paths, and content hashes or a retrievable patch/snapshot of local changes used by the lane. A commit alone does not identify integrated local work. Confirm those inputs are present in a new worktree before dispatch; do not assume a branch checkout includes them. Without Git, record the source paths, relevant content identity, and disjoint file reservations; do not create a repository merely to use this workflow.
4. For GitHub issue work, fetch each candidate issue's body, comments, assignments, linked branches, and pull requests. Treat labels as triage hints, not proof of scope or actionability.
5. Identify active contributor handoffs, shared subsystem ownership, and existing branches or worktrees for the same issue.
6. Account for every pre-existing change before creating or cleaning anything.

Never reset, clean, overwrite, delete, or repurpose an existing dirty worktree or branch. Preserve unknown work, classify it, and ask the owner when its disposition changes the plan. Create new worktrees from the verified base rather than from an arbitrary current checkout.

Historical summaries can explain intent, but live repository and GitHub state determine current ownership.

## Build the conflict matrix

For each candidate lane or issue, record:

- confirmed behavior and expected result;
- likely files and subsystem;
- reproduction or acceptance path;
- overlap with other issues;
- overlap with active collaborator work;
- required host resources or interactive validation;
- disposition: independent lane, coupled lane, sequential, defer, or clarification needed.

Parallelize only genuinely disjoint ownership. Sequence broad or cross-cutting changes after focused lanes. When multiple issues require the same files and one atomic solution, keep them in one coupled lane and explain why. Do not bundle adjacent visual or product redesign into a behavior-repair lane.

## Isolate and dispatch each lane

For Git issue implementation, use one worktree and topic branch per independent lane, following repository conventions. For non-Git work or authorized shared-workspace work, reserve disjoint files explicitly and keep integration files coordinator-owned. Read-only analysis can share source files. A worker prompt must include:

- the relevant accepted requirements and exact bounded question or expected behavior;
- assigned source paths or worktree, plus verified base SHA and relevant dirty-source identity when applicable;
- allowed files or subsystem and forbidden areas, including the coordinator-owned continuity packet;
- direct reproduction and proportionate completion checks;
- execution boundary for builds, GUI, browser, and desktop use;
- authorized stopping point for commits and GitHub actions;
- instruction to stop and report when the fix crosses its boundary.

Workers remain inside their assigned paths or worktree. They do not edit another lane, spawn nested agents, create extra branches or worktrees, merge shared branches, or publish unless explicitly assigned and authorized. The orchestrator must not edit files reserved to an active worker.

Prefer a self-contained bounded brief and exact artifact paths to repeatedly forking the full conversation. Include enough user intent and constraints for the worker to judge its assignment correctly. Reuse a suitable worker for follow-ups instead of spawning duplicate investigations.

Worker returns should be compact and evidence-linked: outcome, exact changed paths, acceptance and check results tied to the inspected source identity, evidence locations, material uncertainty or contradictory evidence, and next action or coordinator decision. Keep raw logs and extensive analysis in existing artifacts. Do not impose a token cap that hides problems. The coordinator inspects relevant evidence and integrates it into its own continuity packet; workers never overwrite that packet.

Do not launch more workers than there are disjoint lanes and available agent slots. Keep an orchestrator slot available for reconciliation and review.

### Shared-host and desktop boundary

A worktree isolates files, not CPU load, memory pressure, GUI applications, browser profiles, keyboard focus, or the owner's interactive desktop. Classify planned execution separately from file ownership:

- lightweight source inspection and repository commands;
- heavy configure, build, or test work;
- application launches and visual reproduction;
- browser or desktop automation;
- foreground input or focus changes.

Respect existing user authorization and project rules for builds, application launches, GUI, browser, foreground input, focus changes, and intrusive compute. Explain upcoming intrusive steps and obtain permission only when not already authorized. Assign scarce host resources to one owner; workers do not independently launch builds or applications when the coordinator owns them. Serialize heavyweight work when concurrency would impair the host.

If one worker becomes intrusive, stop or steer that activity while preserving safe unrelated lanes. Do not terminate unrelated agents, processes, or work merely because one execution boundary was crossed.

## Review proportionally

The orchestrator owns verification of each lane from current artifacts rather than trusting a completion message. It may explicitly delegate checks or review to an independent verifier with named ownership, source identity, acceptance questions, evidence locations, and host limits. That verifier did not implement the work being judged. Reserve each scarce host resource to one owner at a time and serialize verification that uses it, while other safe lanes continue. The orchestrator reconciles findings and acceptance gaps before integration or closure, and refreshes affected checks when integrated source changes invalidate earlier evidence:

1. Inspect changed artifacts or full diff and remaining processes, plus branch and commit state when applicable.
2. Confirm every changed file belongs to the assignment.
3. Run the smallest checks that exercise the changed behavior. Build only the affected target when a build is relevant.
4. Exercise the real workflow when available and authorized.
5. Use existing focused checks. Add a narrow regression check only when permitted by project instructions and useful for the concrete failure.
6. Recheck blast radius, collaborator overlap, and unresolved limitations.

A build, source inspection, screenshot, synthetic fixture, or test count is not by itself proof of a real hardware, private-data, gesture, timing, or appearance-dependent workflow. Do not create broad validation frameworks, CI expansion, policy machinery, or evidence registries without a concrete need and owner approval.

For gesture, timing, or appearance-dependent issues, use the owner-run publication gate in [Interactive GUI validation loop](references/interactive-gui-validation-loop.md). Hold only the failing lane and keep unrelated passing lanes moving.

## Publish focused changes when authorized

When publication is within the authorized stopping point:

1. Push only the reviewed lane branch.
2. Open one pull request per independent atomic change against the agreed base branch.
3. Include root cause, behavior changed, focused evidence, remaining limitations, and `Fixes #N` only when merge should close the issue.
4. Keep unrelated issues separate. Coupled issues may share one pull request only when they truly require one solution and repository policy allows it.
5. Use a disposable local integration branch when combined behavior needs checking; do not turn it into a combined pull request by default.
6. Do not merge, enable auto-merge, release, or close issues without the required owner or maintainer approval.

If the owner asks to formalize the workflow, keep durable collaboration guidance concise and publish it separately from issue fixes. Do not create repository-process documentation merely because parallel work occurred.

## Maintain continuity and report

Once the owner authorizes an orchestration pass, ordinary preflight and wave updates are informational. Continue safe in-scope work through the authorized stopping point. Pause only the action that needs a new decision or permission, and continue disjoint safe work when possible.

At consequential lane changes and before compaction or a fresh-session handoff, update the coordinator-owned continuity record with the accepted objective and acceptance gaps, exact authoritative plan path, user constraints, current evidence paths, lane ownership and status, next executable action, and blocked actions. Record the verified base SHA and remote permissions when applicable. Treat workers and old summaries as evidence sources, not replacements for the accepted plan. Put local orchestration artifacts in the repository's designated ignored local-work directory. Track only plans deliberately intended as shared project artifacts.

Report issue dispositions, worktrees and branches, root causes, focused evidence, blocked or deferred work, collaborator-owned areas left untouched, and any published links. Separate bug repair from enhancement proposals. Stop at the authorized scope boundary.

## Active collaborator handoffs

Treat an assigned or volunteered contributor's unfinished implementation as intentional handoff state. Read the issue conversation before diagnosing duplicate-looking implementations. When canonical and experimental source families coexist, determine which is compiled and whether cleanup is already part of the handoff. Do not create a third implementation or canonicalize the work before behavior and ownership are settled.

For an example involving active handoff protection, conflict grouping, and repository-process publication, read [EtherPlot collaboration example](references/etherplot-collaboration-example.md). Recheck all live issue numbers and ownership claims before adapting it.

## Maintain this skill

When a source repository is supplied, make revisions there and compare installed-only changes before syncing the package outward. Keep the description applicable to engineering work without GitHub. Automatic discovery must remain enabled unless the user requests explicit-only invocation, but selection never overrides restrictions on delegation.
