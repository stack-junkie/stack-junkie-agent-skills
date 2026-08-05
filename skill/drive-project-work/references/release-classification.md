# Release classification

Use this reference only after a task changes project artifacts or when evaluating release readiness.

## Change matrix

| Change | Product version | Product changelog |
|---|---:|---:|
| Read-only investigation, explanation, audit, or plan | No | No |
| Unaccepted product decision or speculative design | No | No |
| Internal governance, agent instructions, or planning mechanics | No | No |
| Tests only with no shipped behavior change | Normally no | Normally no |
| Internal refactor that demonstrably preserves behavior | Normally no | Only if operationally relevant to users or maintainers |
| User-facing documentation distributed with the product | Follow repository policy | Yes when users need the correction |
| Compatible product bug fix | Patch or next prerelease | Yes |
| Compatible user-visible capability | Minor or next prerelease | Yes |
| Packaging, installation, or upgrade behavior | Patch/minor or next prerelease | Yes |
| Public API, public schema, or persisted-state change | SemVer impact or next prerelease | Yes |
| Dependency change affecting behavior, licensing, or distribution | SemVer impact or next prerelease | Yes |
| Breaking behavior or incompatible data/API change | Major, or explicit pre-1.0 policy | Yes |
| Tag, publication, or distribution only | Use the prepared version | Finalize the release entry |

Repository-specific rules override this matrix when they are explicit and current.

## Prerelease cadence

For a maintained alpha product, increment `alpha.n` once for a coherent verified checkpoint that changes shipped behavior. Do not increment for each prompt, turn, worker, commit, failed attempt, plan, or governance-only edit.

Change the base version, such as `0.3.0` to `0.4.0`, only when the intended release line or compatibility promise changes.

## Changelog content

Include:

- new user capabilities;
- changed user-visible behavior;
- fixed user-visible failures;
- compatibility, persistence, packaging, installation, or migration effects;
- dependency or legal changes users or distributors need to know.

Exclude:

- agent activity or orchestration;
- implementation file lists;
- test maintenance as an end in itself;
- internal planning and governance;
- raw verification transcripts;
- claims broader than the verified result.

Prefer the repository's existing changelog format. For a new maintained repository, default to Semantic Versioning and a Keep a Changelog structure.

## Checkpoint versus release

A commit and authorized branch push create a recoverable checkpoint. A tag, protected-ref update, signed artifact, publication, distribution, store submission, or release announcement is a separate release action and requires its own authority.
