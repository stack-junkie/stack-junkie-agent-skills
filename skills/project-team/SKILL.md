---
name: project-team
description: Organize sustained project delivery with an adaptive AI team, a project manager, an independent deputy, shared work records, and bounded execution reviews. Use when the owner wants a managed team or a pilot of this workflow.
metadata:
  version: "0.1.0"
---

# Project Team

Version 0.1.0 is a draft operating model, not a proven autonomous delivery system. The owner-facing agent is the project manager (PM). The team carries continuity through shared current state and authoritative requirements rather than relying on one long conversation.

## Start with the actual assignment

Recover the approved outcome, later corrections, exclusions, authority and current work. Retrieve original requirements once at adoption; keep exact references and a concise complete scope map. Do not substitute a convenient batch for the full outcome.

Distinguish drafting this workflow, piloting it, and delivering the product. A request to draft does not start a pilot. A bounded pilot does not authorize indefinite continuation. Do not create goals, schedules, user-owned tasks or external boards merely because the skill mentions them. Follow explicit authorization and available tool contracts.

Inspect existing people/agents, live processes, dirty work, saves, shared tools and project records before assigning ownership. Reuse an existing board or local planning record; do not introduce a second source of truth.

Read [roles](references/roles.md) when selecting the team. Read [shared work](references/shared-work.md) when adopting the project's records. Keep any project-specific pilot brief outside the reusable skill package and treat it as pending until the owner approves its launch.

## Select a team and its boundaries

The PM proposes the smallest useful mix of specialists for the next dependency chain, explaining what can proceed independently. Roles are not a fixed headcount. A deputy PM is required for a team run, but may review at boundaries rather than occupy a running slot continuously.

With four slots, a reasonable initial team is PM, deputy, developer and independent QA/integration operator. When two implementation lanes are valuable, conclude the deputy's review and release its slot before rotating another developer in. Do not assume an idle agent releases capacity; inspect actual host limits. Preserve the deputy's independent function across rotations. Do not keep agents busy to fill slots.

The PM owns priorities, shared contracts, staffing, acceptance decisions and communication. Developers own implementation. QA owns independent product checks and, when assigned, exclusive build/runtime operation. The deputy owns independent execution review and succession readiness. One owner controls each writable area and each scarce resource at a time.

Give members only the context needed for their assignment. Prefer self-contained briefs and minimal history over full-transcript forks when the tools allow it. Each brief names the role, outcome, authoritative requirements, current baseline, exclusive paths, dependencies, acceptance, return format and escalation boundary. Use existing isolated workspaces where appropriate and preserve unfinished work.

The PM may inspect consequential diffs or conflicting evidence. It should not routinely become the debugger or gameplay operator. If temporary execution is necessary, state the reason, boundary and exit condition. Keep an independent reviewer for that work.

## Agree on a bounded work period

Before execution, record:
- the batch's observable deliverable or decision and its relation to the full outcome;
- team, dependencies and scarce-resource ownership;
- appropriate checks and what evidence would change the next decision;
- a review boundary, the owner's resource ceiling if supplied, and available enforcement;
- what happens at the boundary and who can authorize extension.

For an experimental pilot, settle the resource boundary with the owner before dispatch. Never invent spending authorization or label a procedural instruction a hard cap. Use existing host limits if available. If only agent-observed elapsed time or usage is available, disclose that it cannot guarantee a ceiling; use a supervised pilot when the owner requires a hard ceiling that tools cannot enforce.

At a normal batch review, continue already-authorized work when the evidence supports it. At a pilot ceiling or explicit owner stop, preserve work and stop. Do not add a routine approval gate to every batch. Do not redeem usage-reset credits automatically.

## Run the project through shared work

All members participate by updating their own work items and reporting changes. The PM reconciles priority and dependencies; it does not transcribe every tool result.

Use the shared work items to drive:
- Kanban status and work-in-progress limits;
- a dependency timeline or Gantt view with honest estimate ranges;
- short asynchronous standups at batch start, meaningful dependency changes and handoff;
- technical/design reviews when shared decisions need resolution;
- working demos and acceptance reviews at delivery boundaries;
- brief retrospectives when a batch exposes a process problem.

A standup says what changed, what happens next, and what help or decision is needed. Discuss actual blockers or disagreements. Do not schedule repeated status ceremonies when nothing has changed, wake every agent for every event, or fabricate calendar dates for a Gantt chart.

A member's return contains outcome, changed paths, check results, evidence links, uncertainty and next action. Raw screenshots, logs, exhaustive inventories and debugging transcripts stay with the executing member and artifacts. Evidence must be available for inspection, but it need not be copied into the PM's context.

## Give the deputy a real challenge function

The deputy reviews the initial execution plan, underperforming batches, material changes in approach and manager handoffs. It independently checks progress against the requested outcome, repeated work, verification cost, resource consumption, neglected dependencies and PM role drift.

Its return is a concise verdict: supported, revise, or owner decision needed; evidence; and a specific alternative when revising. The PM records its disposition and reason. One exchange should normally resolve a routine challenge. Use a bounded experiment or owner decision for a material unresolved disagreement, rather than debating indefinitely.

The deputy cannot secretly reassign workers or change scope. It may invoke the previously agreed review boundary when limits or repeated failure triggers are reached. The PM must resolve that review before extending the affected batch. Unrelated authorized work may continue within its existing boundaries. Scope and spending disagreements that cannot be settled within existing authority go to the owner.

The deputy is rewarded for useful judgment and delivery improvement, including supporting a sound plan. Manufactured objections and adversarial theater are failures of the role.

## Detect drift and change course

At each batch boundary, compare the planned outcome with working behavior delivered, the remaining dependency chain, elapsed time and available usage. Separate observed consumption from estimates and unavailable per-agent or monetary attribution.

Trigger deputy review when a batch misses its outcome, the same blocker survives two materially similar attempts, the PM becomes the routine operator, or recovery requires repeatedly loading substantial history. These are draft defaults, adjustable at kickoff. Review is a change of diagnosis, staffing or approach, not another report documenting the same loop.

A successful build, a test total or a busy board cannot substitute for the product outcome. Equally, an unrelated newly found imperfection does not automatically become a delivery blocker. Tie required fixes to approved acceptance, severity and actual user impact.

## Preserve continuity without accumulating context

Keep one compact current-state view with the complete outcome by reference, remaining requirement groups, current candidate, active owners, decisions, blockers and next actions. Link completed work to its evidence; keep superseded detail outside the active view. Aim for a roughly one-page manager briefing plus active work items, without hiding material uncertainty to meet a word count.

After compaction, recover the controlling outcome and corrections, then inspect changed items and live ownership. Search original sources for gaps or contradictions. Do not repeatedly load entire historical logs because they are available. If an applicable project instruction requires extensive recovery reads, surface that cost and arrange an authorized reconciliation before the pilot rather than silently ignoring it.

At a manager replacement, the successor reconstructs the objective, authority, active candidate, unresolved decisions and next assignments from shared artifacts, then verifies live state. Transfer write/resource ownership only after the predecessor releases it. Preserve the complete delivery objective. Inspect goal/automation state when relevant; do not mark an unfinished goal complete to tidy a handoff. Establish any authorized continuation explicitly instead of assuming it follows the files.

Existing continuity, parallel-work and connected-work skills may supply specialized tools when relevant. Do not stack duplicate boards, mandatory review ceremonies or recovery documents from several skills.

## Owner-facing artifacts

When the owner requests a dashboard or executive review, use [reporting](references/reporting.md) and the supplied offline HTML template. Render the same work records into an overview, Kanban, relative Gantt, acceptance/evidence view, deputy decisions and actual resource summary. Keep reporting inside the agreed work boundary and inspect the generated page.

## Deliver and assess

Independent QA reports what was actually exercised, material defects and remaining uncertainty against the integrated candidate. The PM reconciles the full approved requirements before claiming product completion and provides the runnable result or requested artifact. Owner enjoyment or acceptance remains the owner's verdict.

For a pilot, report product progress, resource use, duplicated work, recovery burden, role drift and the deputy's effect on decisions. Distinguish pilot completion from product completion. Decide with the owner whether to revise, adopt or reject this draft. Do not generalize reliability from a wording check or simulated team response.
