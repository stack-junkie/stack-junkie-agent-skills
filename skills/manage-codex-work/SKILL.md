---
name: manage-codex-work
description: Review and coordinate work across Codex conversations from the current chat. Use when the user says "use the coordinator," "run Thread Steward," asks what needs attention across chats, wants related or moved conversations reconciled, wants work parked or resurfaced, or wants validation theater and stalled agent work identified before deciding what to do next.
---

# Manage Codex Work

Act as Thread Steward inside the current Codex conversation. Do not open a separate dashboard, start a persistent service, schedule background work, or use Computer Use.

## Build a current review

Run the bundled read-only scanner:

```shell
python scripts/thread_steward.py scan --days 14
```

Resolve the bundled script relative to this skill directory. The scanner uses Codex's local thread interface, reads recent conversations plus older loaded or explicitly tracked conversations, and emits compact JSON. It contains no turn-start, steering, interrupt, archive, or delete operation. When Codex exposes the invoking thread ID, the scanner keeps that conversation only as a relationship anchor and labels it `current` so an in-progress coordinator turn cannot appear under `NEEDS YOU`.

Treat scanner categories as evidence hints, not final judgment. Read the returned snippets and relationship candidates. Refresh the scan when another conversation may have changed while preparing the review.

## Reconcile workstreams

Group conversations only when the evidence supports one continuing objective.

Strong evidence includes:

- an explicit move, takeover, continuation, or predecessor statement;
- a parent or fork relationship;
- the same distinctive issue, artifact, feature, or requirement set;
- a later conversation clearly assuming ownership of an earlier unfinished task.

Do not merge conversations solely because they share a repository or broad topic. If uncertain, show every instance under `MAY BE RELATED` and ask the owner to confirm the relationship. Keep confirmed owner requirements separate from assistant proposals, implementation evidence, and acceptance.

Choose the canonical conversation from explicit owner direction. Otherwise prefer the latest conversation that clearly owns the objective and contains the newest requirements. Never hide a conflicting active conversation.

Record an owner-confirmed relationship with:

```shell
python scripts/thread_steward.py state relate --workstream-id <id> --title <title> --canonical <thread-id> --related <thread-id> [--related <thread-id>]
```

## Present one decision inbox

Use this order and omit empty sections:

1. `NEEDS YOU`
2. `AT RISK`
3. `WORKING`
4. `PARKED`
5. `DUE TO RESURFACE`
6. `MAY BE RELATED`

Keep each item compact:

```text
N1. Short workstream title
    Canonical: conversation name or recognizable opening
    State: one verified sentence
    Why now: one sentence

    A. Recommended answer
    B. Alternative
    C. Park
```

State when the scan was performed. Give one recommended answer whenever evidence supports it. Do not call work complete merely because an assistant claimed completion. Distinguish direct observation, implementation evidence, tests, assistant claims, and owner acceptance.

## Apply the Reality Guard

Place a workstream under `AT RISK` when current conversation evidence shows:

- validation machinery replacing direct observation of a visible or interactive result;
- repeated commands or planning without changed inputs;
- proxy completion based on builds, tests, screenshots, or self-written rubrics;
- scope substitution toward a more measurable adjacent task;
- self-certification without owner acceptance;
- growing auxiliary work while the requested product surface remains untouched.

Do not treat ordinary focused tests as theater. For a visible UI outcome, recommend opening and inspecting the real interface before creating new validators. Draft a correction for the owner to approve, but do not steer another conversation in the read-only release.

## Park and resurface

Park a workstream with:

```shell
python scripts/thread_steward.py state park --workstream-id <id> --title <title> --canonical <thread-id> --reason <reason> --trigger-type <next_review|date|dependency|manual> [--trigger-value <value>] --original-instruction <owner text>
```

Parking an idle item is immediate. If current evidence shows an active turn, describe it as pending until that turn finishes. Do not interrupt it.

Parked items leave the ordinary inbox. A `next_review` or due `date` trigger returns under `DUE TO RESURFACE`. Dependency and manual triggers remain parked until explicitly resumed:

```shell
python scripts/thread_steward.py state resume --workstream-id <id>
```

Close only the local workstream record:

```shell
python scripts/thread_steward.py state close --workstream-id <id>
```

Never archive or delete a Codex conversation when closing a workstream.

## Respect the action gate

This release is read-only toward other conversations. It may scan threads and record local owner decisions, relationships, or parking state. It must not send, steer, interrupt, archive, or delete across chats.

When the owner answers inbox items, prepare the exact destination and minimal context-wrapped message as a batch preview. State plainly that dispatch remains disabled until the owner accepts the live read-only inbox and the action slice is implemented.
