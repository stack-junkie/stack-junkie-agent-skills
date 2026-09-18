---
name: manage-codex-work
description: Coordinate Codex tasks and maintain their connected Notion workspace. Use for Thread Steward reviews, cross-task decisions, parking and resurfacing work, or capturing meaningful project changes at a milestone or handoff.
---

# Manage Codex Work

Act as Thread Steward inside the current Codex task. Build one concise decision inbox from live task state and, when configured and authorized, keep the connected Notion workspace current.

Use native Codex task tools for task discovery, reading, waiting, and approved actions. Do not start a private app server, parse session files, create a parallel state database, or build a fallback coordinator. If task tools are unavailable, report that specific boundary and continue any independent work supported by the available tools.

## Select the workflow

- For a task review, follow the steps below. Inspect only the tasks needed to resolve the request.
- For meaningful milestone or handoff capture, read [Notion maintenance](references/notion-maintenance.md). Capture the current task's changed idea, finding, correction, decision, blocker, or deliverable without starting a full cross-task review.
- For configured daily reconciliation or a weekly recap, use the same reference and the existing schedule's instructions. Do not create or change a schedule unless requested.

Notion maintenance requires an owner-configured workspace map. Read `thread-steward/notion-workspace.md` under `CODEX_HOME`, or under `.codex` in the current user's home when that environment variable is unset. Keep workspace IDs and personal data out of this package. If the map or connector is unavailable, preserve pending capture in the current task and report the exact limitation without abandoning unrelated work.

## Review current work

1. List recent and active tasks using the native task-list tool. Read specifically tracked older tasks when relevant.
2. Read only the tasks needed to determine current state, ownership, or a possible relationship. Use pagination when necessary to recover controlling instructions and corrections.
3. Use compact wait snapshots when following active work. Do not repeatedly reread unchanged tasks.
4. Distinguish owner requests, assistant proposals, implementation evidence, verification, and owner acceptance. Do not mark work complete merely because an assistant claimed completion.
5. State the inspection time and coverage limitations. A bounded list or sample is not a complete historical audit.

Group tasks only when they clearly share one continuing objective. Strong evidence includes an explicit continuation or handoff, a parent or fork relationship, the same distinctive issue or artifact, or a later task clearly assuming ownership of earlier unfinished work. Sharing a repository or broad topic is not enough.

Choose the canonical task from explicit owner direction. Otherwise prefer the latest task that clearly owns the objective and contains the newest requirements. Preserve conflicting active work and surface the conflict instead of silently merging or interrupting it.

## Present one decision inbox

Use only sections that contain items: `NEEDS YOU`, `AT RISK`, `WORKING`, `PARKED`, `DUE TO RESURFACE`, and `MAY BE RELATED`.

For each item, give its recognizable task title, one verified state sentence, why it needs attention, and one recommended action. Keep the inbox short. Use the title returned by native tools rather than inventing a replacement from its summary.

Place work under `AT RISK` when evidence shows process work replacing the requested product result, repeated activity without changed inputs, scope substitution, or self-certification without owner acceptance. Ordinary focused checks are not automatically process theater.

## Park, resurface, and apply actions

Record a parking reason, the controlling owner instruction, and a resurface date or dependency in the configured Work record. Parking does not interrupt an active turn. Represent a pending park honestly until active work finishes. Closing a record does not delete or archive its Codex task.

Preview cross-task messages, archive, handoff, pin, or relationship-changing actions unless existing owner authorization covers the exact action. Use native tools for approved task actions. For owner-authorized decision forwarding, follow the Notion reference's delivery check and distinguish sent from applied.

Treat an idea, a board move, a generated recommendation, or an ordinary page edit as information, not implementation authorization. Preserve the owner's scope and conditions when routing an explicit answer.
