# EtherPlot collaboration example

This reference captures one concrete application of the class-level workflow. Re-check live repository and GitHub state before reusing any issue number or ownership claim.

## Context

A coworker volunteered to finish EtherCAT parity. The unfinished handoff was intentionally merged into `main` because the branch also contained unrelated application fixes. Issue discussion documented both the handoff and temporary architecture.

The tree contained canonical EtherCAT files and parallel `robot/*_parity.cpp` files. CMake removed canonical files from the active source list and substituted parity files. Both families existed on disk, but only one family was active. The coexistence was already tracked as cleanup after parity, not a new duplicate-implementation bug.

## Conflict grouping

A safe first wave separated:

- annotation Undo crash: annotation/history files;
- tab-group movement bug: `tabbedplotwidget*` group logic;
- stale build identity: narrow top-level CMake/build-identity input.

Later-wave candidates included theme propagation, signal drag/drop, and Linux warning cleanup because they were broader or needed ownership discovery.

Deferred work included EtherCAT parity itself, loading/shutdown paths changed in the handoff, and Robot preset persistence that might overlap workspace integration.

The key rule was not the specific grouping. It was to use issue comments plus likely file ownership to prove independence before launching workers.

## Preflight deltas and behavior clarification

The live open-issue inventory exposed two broad Golden-removal bugs that the prepared handoff prompt had neither scheduled nor explicitly excluded. Because both issues predated the prompt, silence could not establish owner intent. They were classified as a later sequential wave rather than ignored or launched beside focused workers. This is the expected response to a prompt/live-scope mismatch: account for the issues, explain their conflict surface, and ask only if inclusion changes the bounded pass materially.

Sparse bug reports also required focused owner clarification before dispatch:

- Annotation Undo: the concrete sequence was roughly four randomly placed rectangle annotations followed by Undo, which crashed immediately.
- Tab groups: Chrome-style membership was the behavioral baseline: reorder within a group; dropping between another group's member tabs joins it; dragging outside removes the tab while preserving the remaining group. The separate complaint that the text prefix looked like a misleading main tab was recorded as visual-design follow-up, not bundled into the movement bug fix.

## Repository process publication

The permanent collaborator workflow was proposed as:

- one issue branch/worktree per independent fix;
- one PR per issue;
- orchestrator review before push/PR;
- focused build and direct workflow evidence;
- maintainer approval before merge or closure;
- `CONTRIBUTING.md` as the collaborator source of truth;
- README and `AGENTS.md` pointers to that document.

The workflow document was published through its own documentation PR. The issue comment to the coworker was deliberately delayed until merge so it could point to a permanent `main`-branch document rather than a provisional branch.

## Durable lessons

- An active handoff on `main` can be intentional; read the issue conversation before diagnosing it.
- Dual source families may be temporary scaffolding with only one active build path.
- Broad UI/loading/warning issues need discovery or sequencing even when their issue labels say `bug`.
- A local integration branch is useful for combined checks, but independent PRs preserve review and rollback boundaries.
- Repository process should guide collaboration without becoming validation theatre.
