# Stack Junkie Agent Skills

Portable skills for coding agents. Install only the skill you want, then invoke it by name or ask for the behavior it provides.

Each directory under [`skills/`](skills/) is a self-contained, independently versioned package that follows the open Agent Skills format: a required `SKILL.md`, a `VERSION`, and only the scripts, references, and assets that skill needs.

## Available skills

| Skill | What it does | Example request |
|---|---|---|
| [`drive-project-work`](skills/drive-project-work/) | Keeps consequential implementation work bound to one checkable slice with current evidence. | `Use $drive-project-work to deliver this fix as one bounded slice.` |
| [`manage-codex-work`](skills/manage-codex-work/) | Reviews recent and active Codex conversations as one decision inbox without silently merging related work. | `Use $manage-codex-work to show what needs my attention across chats.` |
| [`stack-junkie-style`](skills/stack-junkie-style/) | Applies and visually verifies the Stack Junkie interface system across web, desktop, mobile, and application UIs. | `Use $stack-junkie-style to redesign and visually verify this app.` |
| [`repo-readiness`](skills/repo-readiness/) | Keeps solo, agent-led Git repositories understandable, secure, documented, and releasable. | `Use $repo-readiness to audit and reconcile this repository.` |
| [`preserve-compaction-continuity`](skills/preserve-compaction-continuity/) | Preserves exact owner context and visibly reports recovery after Codex compaction. | `Use $preserve-compaction-continuity to install transcript-backed compaction recovery.` |

## Install

The easiest cross-client option is the open [`skills` CLI](https://github.com/vercel-labs/skills). It detects supported agents and installs only the skill you select.

List the skills without installing anything:

```shell
npx skills add stack-junkie/stack-junkie-agent-skills --list
```

Install one skill globally:

```shell
npx skills add stack-junkie/stack-junkie-agent-skills --skill stack-junkie-style -g
```

Replace `stack-junkie-style` with any name in the catalog. To target a particular client instead of using automatic detection, add `--agent codex` or `--agent claude-code`.

Install every skill only if you actually want the whole collection:

```shell
npx skills add stack-junkie/stack-junkie-agent-skills --skill '*' -g
```

T3 Code uses the skills installed for its selected underlying provider, so it does not need a separate T3-specific package.

### Manual install

If you do not use Node.js, download or clone the repository and copy only the desired `skills/<skill-name>/` directory into a skill location supported by your agent. Common user-level locations include `~/.agents/skills/` for Codex and `~/.claude/skills/` for Claude Code.

On Windows, the repository installer copies and verifies one package:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install_skill.ps1 -Name stack-junkie-style
```

For `drive-project-work`, explicitly include its Codex lifecycle hook:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install_skill.ps1 -Name drive-project-work -InstallCodexHook
```

## Use

Invoke a skill explicitly:

```text
Use $stack-junkie-style to simplify and restyle this application's UI.
Use $repo-readiness to prepare this repository for release.
Use $drive-project-work to deliver this change as one bounded slice.
Use $manage-codex-work to review my recent and active Codex conversations.
```

Compatible agents may also select a skill automatically when a request clearly matches its description.

After installing `preserve-compaction-continuity` for Codex, preview and apply its user-level hook setup from the installed skill directory:

```shell
python scripts/manage.py install
python scripts/manage.py install --apply
```

The manager preserves unrelated hooks and recovery packets. Review changed hook definitions through `/hooks` when Codex requests trust confirmation.

## Validate the collection

For contributors, from the repository root:

```shell
python scripts/check_all.py
python scripts/repo_policy.py verify --repo .
```

The full repository verification requires Gitleaks. Before running `verify` in an unfamiliar clone, inspect the commands in `.repo-policy.json` because they execute as trusted repository code.

Enable the tracked local hooks in a clone with:

```shell
git config core.hooksPath .githooks
```

## Releases

Every `skills/<name>/VERSION` is the source of truth for that independently installable skill. Bump only a skill that changed, and record its version in the root `CHANGELOG.md`. Skill release tags use `<skill-name>@<version>`.

Root `VERSION` identifies the collection snapshot and changes only for a collection release. Ordinary notable changes go under `[Unreleased]` in `CHANGELOG.md`. Collection release tags use `v<version>`, and preparation requires the owner's exact next SemVer:

```shell
python scripts/repo_policy.py prepare-release --repo . <exact-version>
```

The command prepares local collection release files only. Committing, skill or collection tagging, pushing, and publishing are separate authorized actions.

## License

MIT. See [`LICENSE`](LICENSE).
