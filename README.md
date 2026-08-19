# Repo Readiness stack-junkie

Personal Codex skill for preparing and governing repositories used primarily by a solo developer working with coding agents.

The skill provides:

- concise rules of engagement for repository edits;
- root `VERSION` as the canonical version source;
- curated Keep a Changelog entries under `[Unreleased]`;
- explicit release versions selected by the owner;
- Conventional Commit messages with a required `Release-Impact` declaration;
- tracked local hooks and a standard-library Python policy checker;
- main-first branch reconciliation and worktree health reporting;
- required redacted Gitleaks checks for staged work, the current tree, and history;
- repository-aware `.gitignore` review and one consolidated cleanup approval;
- required practical READMEs with full-document stale-content review whenever they are touched;
- no GitHub Actions by default.

## Install

```powershell
scripts\install_skill.cmd
```

The install target is `C:\Users\stack-junkie\.codex\skills\repo-readiness`.

## Validate

```powershell
scripts\run_python.cmd scripts\repo_policy.py audit --repo .
scripts\run_python.cmd scripts\repo_policy.py repo-health --repo .
scripts\run_python.cmd scripts\repo_policy.py scan-secrets --repo . --scope history
scripts\run_python.cmd scripts\repo_policy.py verify --repo .
```

## Use

Invoke the skill explicitly:

```text
Use $repo-readiness to prepare this project as one of my repositories.
```

For an existing repository, the skill audits and adapts the current conventions before adding anything. For a new versioned project, it asks for the exact initial version. New skill repositories may start at `1.0.0` without another version question.

Maintained products, libraries, tools, and skills must have a concise README explaining what the project does, how to install or run it, and its essential usage. Whenever the skill changes a README, it checks the complete document against the live repository and repairs stale commands, paths, configuration, behavior, links, and limitations.

Gitleaks is required. On Windows, install it with:

```powershell
winget install --id Gitleaks.Gitleaks --exact
```

When asked to reconcile a messy repository, the skill first produces one branch and worktree disposition table. No branch, worktree, remote reference, or unique commit is deleted before the owner approves that complete table and a recovery bundle is verified.

## Design basis

- [OpenAI skills](https://learn.chatgpt.com/docs/build-skills) for concise, progressively disclosed workflows with deterministic scripts.
- [OpenAI AGENTS.md guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md) for durable global and project instructions.
- [Semantic Versioning](https://semver.org/) for release-number meaning.
- [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) for curated notable changes and an `[Unreleased]` section.
- [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for machine-readable commit intent.
- [Git hooks](https://git-scm.com/docs/githooks) for local enforcement.
- [Git branch](https://git-scm.com/docs/git-branch) and [Git worktree](https://git-scm.com/docs/git-worktree.html) for reconciliation facts.
- [Gitleaks](https://github.com/gitleaks/gitleaks) and [GitHub push protection](https://docs.github.com/en/code-security/concepts/secret-security/push-protection) for secret prevention.
- [GitHub gitignore templates](https://github.com/github/gitignore) for curated stack-specific ignore rules.
- [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) as an optional remote boundary when local hooks are insufficient.
