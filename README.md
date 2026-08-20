# Stack Junkie Agent Skills

Three portable skills for coding agents. Install only the skill you want, then invoke it by name or ask for the behavior it provides.

Each directory under [`skills/`](skills/) is a self-contained package with a `SKILL.md`, passive version metadata, and only the scripts, references, and assets needed for its actual behavior.

## Available skills

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
