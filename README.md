# Stack Junkie Agent Skills

Portable skills for coding agents. Install only the skill you want, then invoke it by name or ask for the behavior it provides.

Each directory under [`skills/`](skills/) is a self-contained package with a `SKILL.md`, passive version metadata, and only the scripts, references, and assets needed for its actual behavior.

This repository is the source of truth for these packages. Make fixes here, reconcile any installed-only repairs, then sync the reviewed source to the installed copies. Older repositories and deployed copies are comparison evidence, not alternate sources to edit instead.

## Available skills

| Skill | What it does | Example request |
|---|---|---|
| [Project Team (draft 0.1.0)](skills/project-team/) | Organizes an adaptive delivery team with a PM, independent deputy, shared work records and bounded execution reviews. | Use $project-team to organize this approved project. |
| [`manage-codex-work`](skills/manage-codex-work/) | Coordinates Codex tasks using native tools and maintains a configured Notion workspace at milestones and scheduled reviews. | `Use $manage-codex-work to show what needs my attention across tasks.` |
| [`parallel-issue-orchestration`](skills/parallel-issue-orchestration/) | Coordinates independent engineering investigations, implementation, reviews, and GitHub issues across agent lanes. | `Use $parallel-issue-orchestration to identify independent lanes early and coordinate them.` |
| [`stack-junkie-style`](skills/stack-junkie-style/) | Applies the Stack Junkie interface system across web, desktop, mobile, and application UIs. | `Use $stack-junkie-style to redesign this app.` |
| [`preserve-compaction-continuity`](skills/preserve-compaction-continuity/) | Preserves exact owner context and restores the active task after Codex compaction. | `Use $preserve-compaction-continuity to install transcript-backed compaction recovery.` |

## Install

The open [`skills` CLI](https://github.com/vercel-labs/skills) can list or install individual packages:

```shell
npx skills add stack-junkie/stack-junkie-agent-skills --list
npx skills add stack-junkie/stack-junkie-agent-skills --skill stack-junkie-style -g
```

Replace `stack-junkie-style` with another name from the catalog. To target a particular client, add `--agent codex` or `--agent claude-code`.

On Windows, the repository installer copies one package and confirms the installed copy matches its source:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install_skill.ps1 -Name stack-junkie-style
```

For `preserve-compaction-continuity` on Codex, use its manager directly from this repository root. It synchronizes both the skill package and the separate hook runtime:

```shell
python skills/preserve-compaction-continuity/scripts/manage.py install
python skills/preserve-compaction-continuity/scripts/manage.py install --apply
python skills/preserve-compaction-continuity/scripts/manage.py status
```

The continuity manager preserves unrelated hooks and recovery packets and backs up replaced files. Running status from this source compares the repository with the deployed package, runtime, and hook definitions. Running it from an installed copy cannot detect drift from this repository. A package copy alone does not update the hook runtime.

## Use

```text
Use $stack-junkie-style to simplify and restyle this application's UI.
Use $parallel-issue-orchestration to coordinate independent engineering lanes early in this task.
Use $manage-codex-work to review my recent and active Codex tasks.
Use $preserve-compaction-continuity to repair automatic recovery after compaction.
```

Compatible agents may also select a skill automatically when a request clearly matches its description. The continuity and parallel skills explicitly allow implicit invocation. Their trigger descriptions put the main use case first because Codex may shorten descriptions in large skill catalogs. Automatic selection remains model-driven, as described in the [official skill documentation](https://learn.chatgpt.com/docs/build-skills).

For projects that routinely need both skills, concise applicable `AGENTS.md` guidance can require early lane assessment and full approval recovery after compaction. It must respect higher-priority delegation restrictions. Recovery hooks preserve evidence even when the skill is not selected; complete requirement recovery and follow-through still need to be checked in the resumed task. Additional agents do not guarantee fewer compactions.

## Version metadata

Root `VERSION` identifies the collection snapshot. Each remaining `skills/<name>/VERSION` identifies that installed skill. These files are passive metadata and change only when the owner requests a release.

## License

MIT. See [`LICENSE`](LICENSE).
