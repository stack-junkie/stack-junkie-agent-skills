# Stack Junkie Agent Skills

Portable skills for coding agents. Install only the skill you want, then invoke it by name or ask for the behavior it provides.

Each directory under [`skills/`](skills/) is a self-contained package with a `SKILL.md`, passive version metadata, and only the scripts, references, and assets needed for its actual behavior.

## Matt Pocock skills trial

This checkout includes editable copies of the 20 engineering and 7 productivity packages from [Matt Pocock’s skills, version 1.3.2](https://github.com/mattpocock/skills/tree/abeeaf95660ba9e8b7c753eb38f441ca707a8823/skills). The [upstream manifest](https://github.com/mattpocock/skills/blob/abeeaf95660ba9e8b7c753eb38f441ca707a8823/.claude-plugin/plugin.json) lists the original package paths. Each imported package lives directly under `skills/<name>/` and carries Matt’s MIT license and a local `VERSION` file for the installer.

Start a project plan with [grill-with-docs](skills/grill-with-docs/SKILL.md). Use [wayfinder](skills/wayfinder/SKILL.md) for decisions across sessions, [to-spec](skills/to-spec/SKILL.md) to collect the agreed decisions, and [to-tickets](skills/to-tickets/SKILL.md) to split the spec into buildable issues. [Ask Matt](skills/ask-matt/SKILL.md) helps choose among the other skills.

Make adaptations here and use the Windows installer below to sync an edited package. When adopting an upstream update, compare the original package at the linked revision with its newer version and retain any local changes.

## Local skills

| Skill | What it does | Example request |
|---|---|---|
| [`manage-codex-work`](skills/manage-codex-work/) | Reviews and coordinates work across Codex tasks using native task tools. | `Use $manage-codex-work to show what needs my attention across tasks.` |
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

After installing `preserve-compaction-continuity` for Codex, preview and apply its user-level hook setup from the installed skill directory:

```shell
python scripts/manage.py install
python scripts/manage.py install --apply
```

The continuity manager preserves unrelated hooks and recovery packets.

## Use

```text
Use $stack-junkie-style to simplify and restyle this application's UI.
Use $manage-codex-work to review my recent and active Codex tasks.
Use $preserve-compaction-continuity to repair automatic recovery after compaction.
```

Compatible agents may also select a skill automatically when a request clearly matches its description.

## Version metadata

Root `VERSION` identifies the collection snapshot. Each remaining `skills/<name>/VERSION` identifies that installed skill. These files are passive metadata and change only when the owner requests a release.

## License

MIT. See [`LICENSE`](LICENSE).
