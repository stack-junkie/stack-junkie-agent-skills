---
name: preserve-compaction-continuity
description: Recover after compaction and preserve the full approved objective during long tasks. Use when starting sustained implementation, resuming work, or repairing lost requirements and transcript-backed recovery hooks.
---

# Preserve Compaction Continuity

Keep the active objective, owner requests, recent conversation, and immediate next action intact when Codex compacts a session.

## Keep the task contract active

At the start of sustained work, identify the user's approved objective, acceptance requirements, scope exclusions, and execution constraints. Keep a concise coordinator-owned current-state record pointing to the original approval or its verbatim canonical project file. Reuse the project's existing plan or handoff when available; do not create a parallel tracking system. Update it when the user changes scope or new evidence changes the next action. Do not rewrite acceptance around a build, diagnostic, worker deliverable, or convenient checkpoint.

After compaction, read the actual controlling approval and later corrections before implementation. Reading the first few lines of a chronological recovery packet is not recovery. Search its user-prompt section for the approval and read the complete relevant message. Reconcile remaining acceptance requirements with current artifacts and worker status. Recent timing instructions steer a lane; they do not erase the broader objective.

Recover ordinary conversational approvals too: when the user says to proceed with a proposed plan, read that referenced assistant plan from the matching transcript or verified project file. The explicit Plan Mode marker is only a retrieval aid. If the approval cannot be established, continue only work supported by the available instructions and ask for the specific missing decision.

Before ending unfinished implementation, check whether the blocker applies to every useful lane. Continue independent authorized work when only desktop access, a build, or one experiment is blocked. If no useful work can proceed, report the exact blocker and unmet requirements. Do not invent activity merely to avoid stopping.

## Preserve evidence before compaction

Use `scripts/continuity_recovery.py` for these Codex hooks:

- `PreCompact` with matcher `manual|auto`;
- `SessionStart` with matcher `compact|resume`.

Allow `PreCompact` to fail closed when it cannot write a recovery packet. Parse transcripts defensively because Codex provides the transcript path but may change its JSONL record format.

Key recovery by the transcript's own `session_meta.id`. Some hosts give workers their parent's hook session ID: accept that tuple only when the transcript metadata establishes the parent relationship, record both identities, and route recovery into the worker's own namespace. Unrelated mismatches fail without overwriting valid recovery. Matching directories or a shared hook session never make a worker transcript authoritative for the root. Do not guess another transcript or relabel a worker as the parent.

Schema 3 stores immutable generation files and publishes their manifest atomically. It hashes the same transcript byte prefix that was parsed and verifies that prefix on recovery while allowing later appends. It pins the last explicit `PLEASE IMPLEMENT THIS PLAN:` approval ahead of recent context when it fits. Larger approvals remain complete in the full packet with a mandatory read instruction. Other forms of approval still require the reconciliation above. Legacy packets without prefix evidence are not reported as verified.

Preserve every genuine user prompt verbatim in the full packet. Preserve the latest twelve user or assistant messages there. Inject up to the latest eight user prompts and latest six user or assistant messages after compaction. Keep whole messages only when applying the handoff character limit, report the actual injected counts, and show an overlapping user message once rather than duplicating it across sections. Also preserve bounded tool evidence, goal records, Git state, the observed context ratio, a transcript hash, and any substantive prior summary content actually exposed in the transcript.

Keep these evidence layers distinct:

- The source transcript contains the complete user and assistant message history observed at snapshot time.
- The full recovery packet contains every user prompt plus bounded recent conversation and work evidence.
- The active handoff contains the smaller injected selection used immediately after compaction.

The injected user-prompt and conversation selections can overlap. Do not add their counts together. Do not describe messages that were omitted from the active handoff as deleted or lost.

## Report recovery visibly

After `SessionStart` with source `compact`, send one concise commentary report before any tool call. Include:

- whether compaction was automatic or manual and the observed context usage when available;
- what is summarized instead of verbatim in the active handoff;
- separate counts for the source transcript, full recovery packet, and active handoff;
- an explicit warning that the injected prompt and conversation selections can overlap;
- why compaction occurred;
- the specific recovered task;
- the exact action being resumed now;
- whether packet and handoff verification succeeded.

Distinguish verified storage and identity from understood intent. Do not announce semantic recovery or completion merely because hashes match. The first resumed action should recover the controlling requirements when they are not already present.

State in plain language that Codex does not expose an exact before-and-after token diff. Summarize omitted categories only from available evidence. Never invent deleted items or an exact token count. Treat short transcript values such as `summary: "auto"` as compaction settings, not as native summary content.

Do not emit the compaction report for an ordinary resume. If recovery data is missing or corrupt, report the concrete failure instead of claiming success.

## Install safely

When the user supplies a source repository, edit its skill package first. Compare installed-only changes and port the applicable fixes into that source before deployment. Run the manager below from the repository's skill directory so it compares the deployment with the intended source. An installed-directory status check cannot establish agreement with a separate repository.

Preview installation first:

```shell
python scripts/manage.py install
```

Apply only after reviewing the detected Codex home, managed paths, and hook events:

```shell
python scripts/manage.py install --apply
```

The manager discovers `CODEX_HOME` or falls back to `~/.codex`, synchronizes this skill, installs a self-contained runtime, merges only the managed hook handlers, preserves unrelated hooks, and backs up replaced state.

Review changed hook definitions through `/hooks` when Codex requests trust confirmation.

## Audit, repair, or remove

Check installation state without reading private recovery contents:

```shell
python scripts/manage.py status
```

Repair drift by applying `install` again. Preview and apply removal with:

```shell
python scripts/manage.py uninstall
python scripts/manage.py uninstall --apply
```

Remove only this skill's installed package, runtime, and hook handlers. Never print prompts, recovery text, secrets, or transcript contents from management commands.

## Protect recovery data

Store recovery packets under `CODEX_CONTINUITY_HOME` when set. Otherwise use `CODEX_HOME/continuity`, falling back to `~/.codex/continuity`. Treat the files as private because they contain prompts and tool excerpts.

Do not delete recovery sessions automatically.

## Verify the deployed behavior

After deployment, run `python scripts/manage.py status` from the repository's skill directory to compare the source package, installed package, runtime, and managed hook configuration. Exercise changed hook behavior with temporary recovery storage, including distinct root and worker transcripts and complete approval retrieval. Keep private transcript contents out of verification output. Use existing focused checks when available; do not create permanent testing or reporting machinery merely to install the skill.

For live validation, invoke `/compact` only when authorized. Confirm the client delivers the recovery context and that resumed work consults the full controlling requirements. Script checks alone do not prove client delivery or model adherence. Skill discovery, hook execution, packet integrity, and understood requirements are separate checks; report only the ones actually observed.
