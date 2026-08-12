# Stack Junkie Agent Skills

Portable agent skills for applying the Stack Junkie interface system and keeping solo, agent-led Git repositories understandable and releasable.

The repository follows the open Agent Skills layout. Each folder under `skills/` is a complete package with a `SKILL.md` entrypoint and only the scripts, references, and assets that skill needs.

## Included skills

### `stack-junkie-style`

Applies and visually verifies Christopher Kvamme's Stack Junkie design system across web, desktop, mobile, and application interfaces. It includes the canonical interactive specimen, design and UX references, approved example screenshots, and a deterministic compliance workflow with proportional `full`, `focused`, and `token` coverage tiers. Visual claims use screenshots while behavioral claims also require runtime evidence.

### `repo-readiness`

Prepares and governs repositories with a simple main-first workflow for solo development led primarily by coding agents. It covers multi-remote repository health, README upkeep, version and changelog policy, local hooks, secret scanning, bounded project verification, and owner-approved branch reconciliation.

## Install

Clone the collection:

```shell
git clone https://github.com/stack-junkie/stack-junkie-agent-skills.git
cd stack-junkie-agent-skills
```

Copy or symlink the desired skill folder into the personal skill directory used by your agent:

| Client | Personal skill directory |
|---|---|
| Codex | `~/.codex/skills/<skill-name>` |
| Claude Code | `~/.claude/skills/<skill-name>` |

For example, in PowerShell:

```powershell
Copy-Item -Recurse -Force .\skills\stack-junkie-style "$HOME\.codex\skills\"
Copy-Item -Recurse -Force .\skills\repo-readiness "$HOME\.codex\skills\"
```

Change `.codex` to `.claude` to install the same canonical packages for Claude Code. T3 Code runs the selected Codex, Claude Code, or other provider harness, so install the skills for the provider selected in T3 Code. No T3-specific copy exists.

## Use

Invoke the skills by name or ask for the behavior they describe:

```text
Use $stack-junkie-style to redesign and visually verify this application's UI.
Use $repo-readiness to audit and reconcile this repository.
```

The skill descriptions also allow compatible agents to select them automatically when the request clearly matches.

## Validate

From the repository root:

```shell
python scripts/check_collection.py
python -m unittest discover -s tests/repo-readiness -p "test_*.py"
python -m unittest discover -s tests/stack-junkie -p "test_*.py"
python scripts/repo_policy.py verify --repo .
```

Gitleaks is required for the full repository verification command. Before running `verify` in an unfamiliar clone, inspect the commands in `.repo-policy.json` because they execute as trusted repository code. Each command has a configurable timeout that defaults to 900 seconds and cannot exceed 3600 seconds.

Enable the tracked local hooks in a clone with:

```shell
git config core.hooksPath .githooks
```

## Releases

Root `VERSION` is the only manually edited version source for the collection. Ordinary notable changes go under `[Unreleased]` in `CHANGELOG.md`. Release preparation requires the owner's exact next SemVer:

```shell
python scripts/repo_policy.py prepare-release --repo . <exact-version>
```

The release command prepares local files only. Committing, tagging, pushing, and publishing remain separate owner-authorized actions.

## License

MIT. See `LICENSE`.
