# Repository Instructions

- Follow the latest owner instruction and inspect the live files needed for the requested change.
- Treat this repository's `skills/<name>/` packages as the source of truth. Review and reconcile any installed-only fixes here before syncing outward. Do not switch to an older repository based on memory. When sync is requested, verify the installed package against this repository and update any separately deployed runtime too.
- Preserve unrelated dirty work and active processes.
- Do not add tests, validators, policy engines, compliance reports, proof registries, audit loops, or local Git hooks unless the owner explicitly requests them.
- Do not turn direct product work into governance, release, or evidence infrastructure.
- Keep verification proportional and embedded in the requested workflow rather than creating permanent machinery.
- Do not stage, commit, tag, push, publish, create a remote, or open a pull request unless requested.

## Agent skills

- Use [GitHub Issues](https://github.com/stack-junkie/stack-junkie-agent-skills/issues) for Wayfinder maps, decisions, specs, and build tickets. See [tracker operations](docs/agents/issue-tracker.md).
- Use the [triage label mapping](docs/agents/triage-labels.md) for incoming work. Wayfinder decision tickets use their own labels.
- Read the [domain documentation guide](docs/agents/domain.md) when planning or changing a project term or architectural decision.
