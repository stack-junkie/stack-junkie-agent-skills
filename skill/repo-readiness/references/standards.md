# Standards and policy rationale

Use these sources when establishing or explaining repository policy. Do not browse them again for routine edits unless current details matter.

## Codex instructions and skills

- [OpenAI skills documentation](https://learn.chatgpt.com/docs/build-skills) defines skills as reusable instructions with optional scripts and references, and recommends progressive disclosure.
- [OpenAI AGENTS.md documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md) establishes global and project instruction discovery. Keep durable repository rules in root `AGENTS.md`, with narrower overrides only where genuinely required.
- [OpenAI subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents) supports bounded delegation. Independent review is useful only when the reviewer receives raw artifacts and is not primed with the desired verdict.

## Versioning

- [Semantic Versioning 2.0.0](https://semver.org/) assigns major to incompatible API changes, minor to backward-compatible functionality, and patch to backward-compatible fixes. It permits prereleases but does not require them.
- SemVer requires a declared public API. Interpret public API broadly for applications: user-visible behavior, file formats, commands, configuration, integrations, automation contracts, and operator workflows.
- [Python Packaging guidance on single-sourcing versions](https://packaging.python.org/en/latest/discussions/single-source-version/) describes one source of truth plus derived or tested mirrors. This workflow uses root `VERSION` as the canonical source because it is language-neutral and easy for agents and scripts to inspect.

## Changelogs and commits

- [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) recommends an `[Unreleased]` section, notable changes, human-readable categories, and explicitly rejects dumping Git logs into changelogs.
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) provides machine-readable commit intent and maps `fix` to patch, `feat` to minor, and breaking changes to major. `Release-Impact` is a local extension used to make the agent's semantic claim explicit and reviewable.

## Enforcement boundaries

- [Git hooks documentation](https://git-scm.com/docs/githooks) defines local hook execution and notes that commit hooks can be bypassed with `--no-verify`. Treat hooks as fast local feedback, not a tamper-proof boundary.
- Deterministic checks can prove syntax, version agreement, changelog structure, and command outcomes. They cannot prove that an agent classified a behavioral change honestly.
- Independent review reduces self-grading but is still evidence, not owner acceptance. Separate implementation, direct exercise, focused verification, independent review, owner approval, and release status.
- Worktrees isolate working directories, not conceptual ownership. Repartition or serialize tasks that need the same files or shared interfaces.

## Repository governance

- [Git branch documentation](https://git-scm.com/docs/git-branch) defines `--merged` as branches fully contained by the target and therefore mechanically safe deletion candidates. Unique commits still require an owner-approved disposition.
- [Git worktree documentation](https://git-scm.com/docs/git-worktree.html) defines linked worktree metadata and `git worktree prune` for stale administrative records. Never prune or remove a live dirty worktree without preserving its contents.
- [Git bundle documentation](https://git-scm.com/docs/git-bundle) supports portable ref backups and verification. Create and verify an all-ref bundle before an approved destructive reconciliation.
- [GitHub branch management guidance](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository) recommends removing merged or stale branches. This workflow keeps `main` primary and uses short-lived topic branches only when they provide isolation.

## Secrets and ignored files

- [Gitleaks](https://github.com/gitleaks/gitleaks) scans Git history, directories, and staged changes. Always request full redaction and fail clearly when the required executable is unavailable.
- [GitHub push protection](https://docs.github.com/en/code-security/concepts/secret-security/push-protection) blocks supported credentials before they reach the remote. Recommend it when available, but keep local scanning because coverage and availability vary.
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) recommends centralized storage, limited access, rotation, and preventing secret propagation through copies and forks. A discovered real credential requires rotation; deleting a file is not remediation.
- [GitHub's gitignore collection](https://github.com/github/gitignore) curates small stack-specific templates rather than exhaustive lists. Merge only rules justified by detected tools and frameworks, and preserve intentional project rules.

## Repository layout

- Follow the repository's existing ecosystem conventions for new work. Do not add a universal naming checker or mass-rename legacy files.
- Preserve build-system layouts. Move files only to solve a concrete problem, and update affected references in the same change.

## READMEs

- [GitHub's README guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes) describes the README as a visitor's starting point for what a project does, why it is useful, and how to use it. It also recommends keeping longer documentation elsewhere.
- [Google's README style guide](https://google.github.io/styleguide/docguide/READMEs.html) calls for an up-to-date top-level `README.md` that explains purpose and practical usage. Treat current repository behavior as the source of truth when repairing stale documentation.

## GitHub

- [GitHub Actions documentation](https://docs.github.com/en/actions/get-started/understand-github-actions) describes workflows as hosted CI/CD automation. Add them only for a concrete hosted need and call the same local verification command.
- [GitHub rulesets documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) describes server-side branch and tag controls. Rulesets are stronger than local hooks for protected remote refs, but they add friction and may depend on repository visibility or plan.
