# Stack Junkie Agent Skills

Skills for coding agents covering interface design, task coordination, delegated delivery, and recovery after context compaction. Install the skill you need, then invoke it by name or ask for the behavior it provides.

Each package under [`skills/`](skills/) contains a `SKILL.md` and version metadata. Some also include agent display metadata, scripts, references, or assets. Runtime and companion-skill requirements vary by package.

This repository is the source of truth for these packages. Make fixes here, reconcile any installed-only repairs, then sync the reviewed source to the installed copies. Older repositories and deployed copies are comparison evidence, not alternate sources to edit instead.

## Matt Pocock skills trial

This checkout includes editable copies of the 20 engineering and 7 productivity packages from [Matt Pocock’s skills, version 1.3.2](https://github.com/mattpocock/skills/tree/abeeaf95660ba9e8b7c753eb38f441ca707a8823/skills). The [upstream manifest](https://github.com/mattpocock/skills/blob/abeeaf95660ba9e8b7c753eb38f441ca707a8823/.claude-plugin/plugin.json) lists the original package paths. Each imported package lives directly under `skills/<name>/` and carries Matt’s MIT license and a local `VERSION` file for the installer.

Start a project plan with [grill-with-docs](skills/grill-with-docs/SKILL.md). Use [wayfinder](skills/wayfinder/SKILL.md) for decisions across sessions, [to-spec](skills/to-spec/SKILL.md) to collect the agreed decisions, and [to-tickets](skills/to-tickets/SKILL.md) to split the spec into buildable issues. [Ask Matt](skills/ask-matt/SKILL.md) helps choose among the other skills.

Make adaptations here and use the Windows installer below to sync an edited package. When adopting an upstream update, compare the original package at the linked revision with its newer version and retain any local changes.

## Local skills

| Skill | What it does | Example request |
|---|---|---|
| [`write-articles` (draft)](skills/write-articles/SKILL.md) | Develops a confirmed brief into a sourced private article in Chris's voice, with independent review and contextual internal links. | `Use $write-articles to develop this article idea.` |
| [`project-team` (draft 0.1.2)](skills/project-team/SKILL.md) | Organizes an adaptive delivery team with a PM, independent deputy, shared work records, and bounded execution reviews. | `Use $project-team to organize this approved project.` |
| [`chief-delegator`](skills/chief-delegator/SKILL.md) | Keeps one lead responsible for the approved outcome, integration, and acceptance while workers handle bounded implementation and review. | `Use $chief-delegator to lead delivery of this approved project.` |
| [`manage-codex-work`](skills/manage-codex-work/) | Coordinates Codex tasks using native tools and maintains a configured Notion workspace at milestones and scheduled reviews. | `Use $manage-codex-work to show what needs my attention across tasks.` |
| [`parallel-issue-orchestration`](skills/parallel-issue-orchestration/) | Coordinates independent engineering investigations, implementation, reviews, and GitHub issues across agent lanes. | `Use $parallel-issue-orchestration to identify independent lanes early and coordinate them.` |
| [`stack-junkie-style`](skills/stack-junkie-style/) | Applies the Stack Junkie interface system across web, desktop, mobile, and application UIs. | `Use $stack-junkie-style to redesign this app.` |
| [`preserve-compaction-continuity`](skills/preserve-compaction-continuity/) | Preserves exact owner context and restores the active task after Codex compaction. | `Use $preserve-compaction-continuity to install transcript-backed compaction recovery.` |

Project Team is an experimental operating model. Its draft version and pilot artifacts do not establish proven autonomous delivery.

## Requirements

- An agent that can load `SKILL.md` packages. Delegation workflows also need agent tools and permission to use them.
- `chief-delegator` composes `parallel-issue-orchestration` and `preserve-compaction-continuity`; make both companion skills available to the agent.
- `manage-codex-work` requires native Codex task tools. Connected capture also needs a Notion connector and an owner-configured workspace map; see [Notion maintenance](skills/manage-codex-work/references/notion-maintenance.md).
- Continuity hook management requires Python and a Codex host that supports the named hooks. The optional Project Team report renderer also uses Python. Both use the standard library.
- The CLI install option below requires Node.js/npm. The local Windows installer uses PowerShell.
- `write-articles` includes optional Node.js 22.18+ helpers. Its Stack Junkie adapter reads the destination's existing parser and dependencies; independent editorial review needs delegation. Trial acceptance and installation are pending.

## Install

The open [`skills` CLI](https://github.com/vercel-labs/skills) can list or install individual packages:

```shell
npx skills add stack-junkie/stack-junkie-agent-skills --list
npx skills add stack-junkie/stack-junkie-agent-skills --skill stack-junkie-style -g
```

Replace `stack-junkie-style` with another name from the catalog. To target a particular client, add `--agent codex` or `--agent claude-code`.

The GitHub commands install the published repository state. To use this checkout, including local changes, run from the repository root:

```shell
npx skills add . --skill stack-junkie-style -g --agent codex
```

On Windows, the repository installer copies one local package and confirms the installed copy matches its source:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install_skill.ps1 -Name stack-junkie-style
```

It defaults to `%USERPROFILE%\.codex\skills`, or `CODEX_SKILLS_DIR` when set. Use `-SkillsDir` to select another installation directory. The installer replaces the existing destination package, so reconcile installed-only changes first. Keep the destination outside this repository's source packages.

For `preserve-compaction-continuity` on Codex, use its manager directly from this repository root. It synchronizes both the skill package and the separate hook runtime:

```shell
python skills/preserve-compaction-continuity/scripts/manage.py install
python skills/preserve-compaction-continuity/scripts/manage.py install --apply
python skills/preserve-compaction-continuity/scripts/manage.py status
```

The continuity manager preserves unrelated hooks and recovery packets and backs up replaced files. Running status from this source compares the repository with the deployed package, runtime, and hook definitions. Running it from an installed copy cannot detect drift from this repository. A package copy alone does not update the hook runtime.

## Use

```text
Use $project-team to organize this approved project and agree on a bounded pilot.
Use $chief-delegator to lead delivery of this approved project.
Use $stack-junkie-style to simplify and restyle this application's UI.
Use $parallel-issue-orchestration to coordinate independent engineering lanes early in this task.
Use $manage-codex-work to review my recent and active Codex tasks.
Use $preserve-compaction-continuity to repair automatic recovery after compaction.
```

Compatible agents may also select a skill automatically when a request clearly matches its description. The continuity and parallel skills explicitly allow implicit invocation. Their trigger descriptions put the main use case first because Codex may shorten descriptions in large skill catalogs. Automatic selection remains model-driven, as described in the [official skill documentation](https://learn.chatgpt.com/docs/build-skills).

For projects that routinely need both skills, concise applicable `AGENTS.md` guidance can require early lane assessment and full approval recovery after compaction. It must respect higher-priority delegation restrictions. Recovery hooks preserve evidence even when the skill is not selected; complete requirement recovery and follow-through still need to be checked in the resumed task. Additional agents do not guarantee fewer compactions.

## Examples and pilots

- [Stack Junkie living showcase](skills/stack-junkie-style/ui/README.md): run the shared web or Qt components in three light/dark preview directions. Version 3.0.0-preview.1 awaits owner visual selection.
- [Life Explosion pilot brief](pilots/project-team-life-explosion-0.1.0.md) and [trial guidance](pilots/life-explosion-team-trials.md): project-specific assignments kept outside the reusable Project Team package.
- [Delivery review](pilots/life-explosion-delivery-review.html) and its [JSON snapshot](pilots/life-explosion-report-data.json): open the HTML locally to inspect the prepared runs, recorded findings, and remaining work. It is a snapshot, not a live project controller.
- [Report authoring](skills/project-team/references/reporting.md): use the supplied renderer and template for another project's real data.

## Maintaining this repository

Edit packages in `skills/<name>/` and keep their linked resources together. Review installed-only fixes before syncing outward. Use the continuity manager when changes also affect its separately deployed hook runtime.

Keep project-specific trials in `pilots/`. Check changed links, commands, and the affected behavior; the repository has no collection-wide build or test runner. See [AGENTS.md](AGENTS.md) for working agreements and [CHANGELOG.md](CHANGELOG.md) for collection history.

### Version metadata

Root `VERSION` identifies the collection snapshot. Each `skills/<name>/VERSION` identifies that package's version; installed copies retain the version they were copied from. These files are passive metadata and change only when the owner requests a release. Current draft work is recorded under `Unreleased` in the changelog.

## License

MIT. See [`LICENSE`](LICENSE).
