---
name: manage-codex-work
description: Review and coordinate work across Codex tasks from the current conversation using native Codex task tools. Use when the user asks what needs attention across tasks, wants related conversations reconciled, wants work parked or resurfaced, or asks to manage Codex work.
---

# Manage Codex Work

Build one concise decision inbox from live Codex task state. Use only native task tools exposed by the current Codex client. Do not start a private app server, parse session files, create a parallel state database, or build a fallback coordinator.

If native task tools are unavailable, say that the task list cannot be inspected from the current client and stop.

## Review current work

1. List recent and active tasks with the native task-list tool.
2. Read only the tasks needed to determine current state, ownership, or a possible relationship.
3. Use compact wait snapshots when following active work. Do not repeatedly reread unchanged tasks.
4. Distinguish owner requests, assistant proposals, implementation evidence, and owner acceptance.
5. Do not call work complete merely because an assistant claimed completion.

Group tasks only when they clearly share one continuing objective. Strong evidence includes an explicit continuation or handoff, a parent or fork relationship, the same distinctive issue or artifact, or a later task clearly assuming ownership of earlier unfinished work. Sharing a repository or broad topic is not enough.

## Present one decision inbox

Use only the sections that contain items:

1. `NEEDS YOU`
2. `AT RISK`
3. `WORKING`
4. `PARKED`
5. `MAY BE RELATED`

For each item, state the recognizable task, one verified state sentence, why it needs attention, and one recommended action. Keep the inbox short.

Place work under `AT RISK` when the current evidence shows process work replacing the requested product result, repeated activity without changed inputs, scope substitution, or self-certification without owner acceptance. Ordinary focused checks are not automatically process theater.

## Apply approved actions

Preview any cross-task message, archive, handoff, pin, or relationship-changing action before applying it unless the owner already gave exact authorization. Use native task tools for the approved action. Never create another coordination runtime to compensate for a missing tool.

Closing a work item does not delete its Codex task. Preserve conflicting active work and report it rather than silently merging or interrupting it.
