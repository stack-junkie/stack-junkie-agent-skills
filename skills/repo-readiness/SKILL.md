---
name: repo-readiness
description: Prepare, audit, reconcile, secure, govern, document, or release a Git repository using Stack Junkie's simple main-first workflow for solo agent-led work. Use when an agent is asked to make a project repo-ready, create or refresh its README, merge or clean up branches and worktrees, reconcile diverged work, evaluate .gitignore, prevent secret leaks, govern agent edits, synchronize canonical versions, curate changelogs, prepare an exact release, configure local hooks, or decide whether GitHub workflows are justified.
---

# Repo Readiness stack-junkie

Build a low-friction repository that coding agents can change safely and the owner can understand quickly.

## Non-negotiable contract

1. Read the live repository before proposing or changing policy.
2. Treat the latest owner instruction and repository `AGENTS.md` as authority. Do not replace established project conventions silently.
3. Preserve unrelated dirty work and active processes.
4. Add no feature, file, document, workflow, abstraction, or organizational layer without a concrete purpose in the requested outcome.
5. Never stage, commit, tag, push, publish, create a remote, or open a pull request unless the user requested that action.
6. Never call self-review independent verification.

## Classify before adding machinery

Classify both the repository and the current work:

- `maintained-product`: shipped or operated software that benefits from releases and a changelog;
- `library-or-tool`: exposes behavior or an interface consumed elsewhere;
- `skill`: reusable agent skill source repository;
- `prototype`: disposable or exploratory code;
- `planning-only`: notes or decisions without a shipped artifact.

Add versioning and release enforcement to maintained products, libraries, tools, and skills. Do not force it onto prototypes or planning-only repositories unless the owner asks.

Classify the current work as:

- `investigation`: read-only evidence gathering;
- `internal`: no user-visible or operator-visible behavior change;
- `notable`: user-visible, operator-visible, compatibility, security, or meaningful performance change;
- `release`: an owner-selected version checkpoint.

Investigations never create release ceremony. Internal changes normally use `Release-Impact: none`. Notable changes update `[Unreleased]` but do not bump the version. Releases change the version exactly once.

## Read-only preflight

Before editing:

1. Resolve the exact repository root and current working directory.
2. Read applicable `AGENTS.md` files and release instructions.
3. Inspect `git status --short --branch`, remotes, branch, tags, existing hooks, version sources, changelog, package manifests, build commands, tests, and `.github/workflows`.
4. Identify unrelated dirty files and exclude them from the work.
5. State the intended files, the requested outcome, the checks that can prove it, and any owner decision that is genuinely required.

Do not ask questions whose answers are available in the repository. Do ask before a material policy choice that the repository and owner have not established.

## Repository setup

Prefer adapting an existing valid process over replacing it. For a repository without a process:

1. Initialize Git on `main` only when the user asked to create or prepare a repository.
2. Use root `VERSION` as the single manually edited version source.
3. Ask for the exact initial version. For a new agent skill only, default to `1.0.0` unless the user specifies another version.
4. Add `CHANGELOG.md` with `[Unreleased]` and Keep a Changelog categories.
5. Create or repair root `README.md` for maintained products, libraries, tools, and skills. Keep it project-specific and practical.
6. Add or merge concise durable rules into root `AGENTS.md`. Do not create a second rules document for the owner to discover.
7. Add `.repo-policy.json`, `scripts/repo_policy.py`, and tracked `.githooks` only for a versioned repository.
8. Configure only the version mirrors genuinely required by build or packaging tools.
9. Configure at least one real project verification command for maintained products, libraries, tools, and skills. An empty command list is incomplete and must fail audit.
10. Treat verification commands as trusted repository code. Inspect them before execution and set `verification_timeout_seconds` only when the 900-second default is unsuitable.
11. Require Gitleaks, review `.gitignore` against the actual stack, run `git config core.hooksPath .githooks`, then audit the result.

Use the bundled scaffold command only when its target files do not already exist:

```powershell
python <skill-dir>\scripts\repo_policy.py scaffold --repo <repo> --project-type <type> --version <exact-version> --init-git
```

Omit `--version` only for a new `skill`, which defaults to `1.0.0`. If files already exist, merge deliberately with `apply_patch`; never force-overwrite them.

## Rules for agent-led edits

Before implementation:

- Convert the request into one bounded outcome without shrinking the user's actual goal.
- Name the owned files or modules when multiple agents are involved.
- Use separate Git worktrees for parallel writers only when file and module ownership is disjoint.
- If two tasks need the same file or shared interface, repartition them or serialize the edits under one writer. Do not use worktrees as permission for conflicting same-file changes.
- Keep one integration owner. Review another agent's diff before integrating it.

During implementation:

- Make the smallest coherent change that fully solves the requested slice.
- Do not reorganize unrelated code, add speculative settings, or create filler UI, docs, tests, or automation.
- Preserve existing behavior unless the request changes it.
- Stop on conflicting edits, ambiguous destructive targets, missing authority, or a required owner decision.

After implementation:

- Run focused verification proportional to risk.
- Exercise the real changed workflow when practical; do not substitute structure checks for behavior.
- Inspect the final diff for accidental files, generated debris, secrets, stale versions, and scope drift.
- Report implemented, directly exercised, focused-verified, independently verified, owner-approved, and released states separately.

## Main-first repository governance

Treat `main` as the normal source of truth. Work directly on it for serial bounded changes. Use short-lived `agent/*` branches only for risky or parallel work unless the repository or active harness establishes another convention. Settle each branch before starting unrelated work.

For "fix," "govern," "clean up," or "reconcile" requests:

1. Fetch current remote-tracking information without changing worktrees. Defer pruning until cleanup is approved.
2. Run the bundled `python <skill-dir>\scripts\repo_policy.py repo-health --repo <repo>` to inventory branches, every configured remote, and worktrees, even if the target has not adopted this policy. Inspect unique commits and conflicts only for branches that are not already merged.
3. Classify every non-main branch as fast-forward, merge, selected cherry-picks, already merged, deliberately retained, or archived then removed.
4. Present one compact table covering each branch or worktree, its disposition, and any destructive action.
5. Treat approval of that complete table as one cleanup approval. Do not expand it to unlisted destructive actions.
6. Before approved deletion of unique committed work, create and verify a dated recovery bundle. Skip the bundle when cleanup only deletes branches Git proves are merged.
7. Never remove a dirty worktree until its uncommitted contents have an approved disposition. Prefer fast-forward integration. Never rewrite published history or force-push unless explicitly approved.
8. Verify main before deleting source branches. Delete only branches proven merged or explicitly approved as abandoned, then prune stale worktree records.

The default branch's upstream remote is governed. Additional upstream or vendor remotes are reported but their independent history is not treated as local branch clutter. The policy command reports Git facts; the agent decides product intent. Never automate the selection or deletion of unique commits.

## Repository hygiene

During onboarding, identify the actual languages, build tools, editors, generated outputs, local secrets, and current untracked artifacts. Merge only relevant rules into the existing `.gitignore`, using GitHub's curated templates as a reference. Preserve `.env.example` and `.env.template`, verify representative paths with `git check-ignore -v`, and never hide tracked secrets or unexplained junk.

Follow the repository's ecosystem naming and layout conventions for new work. Do not build a generic renaming engine, mass-rename legacy files, or reorganize a working tree merely to make it look tidy. Move files only to solve a concrete ambiguity, duplication, broken-tooling, or discoverability problem.

## README policy

Require `README.md` for maintained products, libraries, tools, and skills. Keep it optional for prototypes and planning-only repositories unless the owner asks for one.

Whenever this skill creates or touches `README.md`, read the entire document before editing and fact-check it against the live repository. Repair stale content anywhere in the file, not only near the requested edit. Check commands, paths, prerequisites, supported platforms, configuration names, defaults, screenshots, links, features, and limitations that the README claims. Remove obsolete instructions and claims. Preserve accurate prose instead of rewriting it for style.

Keep the README concise and useful. Include:

- the project name and what it does;
- installation, setup, build, or run instructions that were verified when practical;
- essential usage or commands;
- only the configuration, safety notes, limitations, and links users actually need.

Do not manually copy the project release version into the README. Omit it, derive it from `VERSION`, or use release metadata so it cannot drift. Do not add roadmap filler, generic badges, duplicated changelog content, internal agent instructions, or chat history.

## Secret protection

Require Gitleaks. Run:

```powershell
python scripts/repo_policy.py scan-secrets --repo . --scope staged
python scripts/repo_policy.py scan-secrets --repo . --scope tracked
python scripts/repo_policy.py scan-secrets --repo . --scope history
```

The pre-commit check runs the staged scan, full verification scans every regular tracked Git index blob, and governance or release work scans history. Keep case-colliding paths and merge-conflict stages independently inspectable. Never follow a working-tree symlink during a tracked scan, and skip submodule entries. Always use full redaction. If Gitleaks is unavailable, fail with installation guidance instead of silently weakening the gate.

If a real credential is found, stop, identify only its rule and location, and require rotation. Treat history rewriting as a separate destructive decision. Allowlist only a narrow fingerprint or path with a preceding `# Reason: ...` comment in `.gitleaksignore`. Recommend GitHub push protection when supported; do not add Actions for it.

## Changelog policy

Maintain `[Unreleased]` during ordinary work. Add only notable outcomes that matter to users or operators.

Use `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, and `Security` where applicable. Write outcome-oriented bullets. Do not paste commit logs.

Exclude:

- prompts, chat history, owner conversation, agent process, or continuation notes;
- tests run, files touched, implementation narration, failed attempts, or review logistics;
- internal refactors and dependency churn with no meaningful behavioral effect;
- vague bullets such as "continued work," "miscellaneous improvements," or "various fixes."

If a change needs explanation but not a changelog entry, put it in the handoff or commit body.

## Commits

Use Conventional Commit subjects and one required footer:

```text
feat(ui): simplify the primary workflow

Release-Impact: minor
```

Allowed values are `none`, `patch`, `minor`, and `major`.

- Use `none` for internal, test-only, build-only, or documentation-only work with no notable external outcome.
- Use `patch` for backward-compatible fixes.
- Use `minor` for backward-compatible capability additions or deprecations.
- Use `major` for breaking changes.
- A `feat` commit must declare `minor` or `major`.
- A `fix` commit must declare `patch` or `major`.
- A breaking `!` or `BREAKING CHANGE:` declaration must use `major`.

The hook requires a staged `[Unreleased]` bullet for non-`none` impact. The impact declaration is a reviewable claim, not proof. A mechanical checker cannot determine whether an agent dishonestly labeled a feature as an internal chore. Review the diff against the declaration, and use an independent reviewer for releases when available.

## Versions and releases

Never infer a release version. If the user has not supplied the exact version for this release, stop release preparation and ask.

For an approved version:

1. Confirm `[Unreleased]` contains the complete curated release notes.
2. Require a clean working tree so the release cannot silently absorb uncommitted or unrelated work.
3. Require settled repository health and a passing full-history Gitleaks scan.
4. Compare the requested version with the public behavior and explain any SemVer mismatch before proceeding.
5. Run `python scripts/repo_policy.py prepare-release --repo . <exact-version>`.
6. Confirm `VERSION`, configured mirrors, and the dated changelog heading agree.
7. Run all repository verification and inspect the release diff.
8. Obtain an independent diff and release-classification review when another agent is available. Give the reviewer the request, raw diff, repository rules, and evidence, but not the desired verdict.
9. If no independent reviewer is available, say so and report self-review only.
10. Commit as `chore(release): <version>` with `Release-Impact: none` only when commit authorization exists. Tag, push, and publish only when each action is authorized.

Do not modify a released version. Correct it in a new release.

## Local enforcement

Treat `scripts/repo_policy.py` as the deterministic policy entry point:

```powershell
python scripts/repo_policy.py audit --repo .
python scripts/repo_policy.py check-staged --repo .
python scripts/repo_policy.py repo-health --repo .
python scripts/repo_policy.py verify --repo .
```

Before `verify`, inspect `.repo-policy.json` verification commands as executable repository code. Each command is limited to `verification_timeout_seconds`, which defaults to 900 and may not exceed 3600 seconds. Release preparation renders every target first and replaces the version, changelog, and configured mirrors as one rollback-protected update.

Tracked hooks provide fast feedback, but all local hooks can be bypassed. The policy script, final diff review, and independent release review are the evidence. Never describe hooks as an absolute security boundary.

## GitHub policy

Create no GitHub Actions workflow by default. Local repositories and single-platform personal tools usually gain little from hosted YAML that repeats local checks.

Recommend one minimal workflow only when at least one concrete need exists:

- remote branch protection requires a status check;
- contributors or remote agents can bypass local hooks;
- multiple operating systems or runtime versions must be tested;
- packages, releases, deployments, or scheduled checks must run remotely.

If approved, make the workflow call the same repository verification command. Do not duplicate policy logic in YAML. Pin third-party actions to an immutable commit for sensitive release or deployment workflows.

GitHub rulesets may block force pushes, tag deletion, or unreviewed changes when the remote is an important boundary. Do not impose mandatory pull requests on a solo private repository without a demonstrated need.

## Handoff

Report:

- repository classification and edit classification;
- files intentionally changed;
- behavior directly exercised and checks run;
- changelog impact and current version state;
- local hook and policy status;
- README status when it was created, changed, or found stale;
- commit, tag, push, remote, pull request, and release status separately;
- independent review status and any remaining owner decision.

Keep the handoff proportional. For branch-only cleanup, omit version, release, hook, and publication details that did not apply.

Read [references/standards.md](references/standards.md) when establishing or changing repository policy, explaining a policy choice, or resolving a version, changelog, commit, hook, or GitHub tradeoff.
