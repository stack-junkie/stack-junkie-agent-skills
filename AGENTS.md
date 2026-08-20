# Repository Instructions

<!-- repo-readiness:v1 -->

- Read the live repository, applicable instructions, and Git state before editing.
- Preserve unrelated dirty work and active processes.
- Add only files, features, documentation, tests, and automation required by the requested outcome.
- Keep `main` as the normal source of truth.
- Use short-lived `agent/*` branches only for risky or parallel work, unless the repository or active harness establishes another convention.
- Settle every task branch by integrating it, deliberately parking it, or reporting it as unresolved before starting unrelated work.
- Run focused checks, exercise the changed workflow when practical, and inspect the final diff.
- Do not stage, commit, tag, push, publish, create a remote, or open a pull request unless requested.
- Treat root `VERSION` as the manually edited collection version source and each `skills/<name>/VERSION` as that independently released skill's version source.
- Bump only skills whose public behavior or packaging changed. Do not bump unchanged skills merely to match the collection version.
- Put notable ordinary changes under `CHANGELOG.md` `[Unreleased]` without bumping the version.
- Require the owner's exact skill or collection version before preparing a release.
- Review the complete README for stale or inaccurate content whenever it is changed.
- Require redacted Gitleaks checks for staged work, tracked files, and repository history when governing or releasing.
- Keep GitHub Actions absent unless a concrete hosted need is approved.
