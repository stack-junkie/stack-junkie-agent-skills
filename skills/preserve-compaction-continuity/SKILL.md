---
name: preserve-compaction-continuity
description: Preserve and restore task continuity across Codex automatic or manual context compaction using transcript-backed recovery packets, lifecycle hooks, and a visible post-compaction report. Use when installing, repairing, or removing compaction recovery; when Codex loses owner requests or the continuation point after compaction; or when a user wants recent messages and current work rehydrated automatically.
---

# Preserve Compaction Continuity

Keep the active objective, owner requests, recent conversation, and immediate next action intact when Codex compacts a session.

## Preserve evidence before compaction

Use `scripts/continuity_recovery.py` for these Codex hooks:

- `PreCompact` with matcher `manual|auto`;
- `SessionStart` with matcher `compact|resume`.

Allow `PreCompact` to fail closed when it cannot write a recovery packet. Parse transcripts defensively because Codex provides the transcript path but may change its JSONL record format.

Preserve every genuine user prompt verbatim in the full packet. Inject the latest eight user prompts and latest six user or assistant messages after compaction. Also preserve bounded tool evidence, prior native summaries, goal records, Git state, the observed context ratio, and a transcript hash.

Do not claim that evidence was deleted when it remains in the recovery packet.

## Report recovery visibly

After `SessionStart` with source `compact`, send one concise commentary report before any tool call. Include:

- whether compaction was automatic or manual and the observed context usage when available;
- what is no longer verbatim in the active handoff, what remains in the full packet, and exact preservation counts;
- why compaction occurred;
- the specific recovered task;
- the exact action being resumed now;
- whether packet and handoff verification succeeded.

State that Codex does not expose an exact native token-removal map. Summarize omitted categories only from available evidence. Never invent deleted items or an exact token count.

Do not emit the compaction report for an ordinary resume. If recovery data is missing or corrupt, report the concrete failure instead of claiming success.

## Install safely

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
