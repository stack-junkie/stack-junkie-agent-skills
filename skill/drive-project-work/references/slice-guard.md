# Slice guard commands

Use these commands only for implementation work. The lifecycle hook supplies the current session id and installed script path at session start and after compaction.

## Begin

Create one compact JSON contract in a single guard invocation. PowerShell example:

```powershell
py -3 "C:\Users\ckvam\.codex\skills\drive-project-work\scripts\slice_guard.py" begin --session "example-session" --cwd "C:\work\example-project" --contract '{"outcome":"Saved projects reopen with the selected data source restored","allowed_paths":["src/project","tests/project"],"acceptance":[{"id":"A1","kind":"command","criterion":"The focused reopen regression passes","command":"ctest --test-dir build -R project_reopen --output-on-failure"},{"id":"A2","kind":"observe","criterion":"The packaged app reopens a representative saved project without losing the source"},{"id":"A3","kind":"owner","criterion":"The owner confirms behavior with the private production file"}],"outside_scope":["Unrelated import formats","Release publication"],"subagents":"reviewer"}'
```

Contract fields:

- `outcome`: one user-visible journey, not the whole project or backlog.
- `allowed_paths`: one to eight paths narrower than the project root.
- `acceptance`: one to five predeclared `command`, `observe`, or `owner` checks.
- `outside_scope`: adjacent work that stays visible but cannot be started in this slice.
- `subagents`: `none` or one bounded `reviewer`. Parallel implementation is a separate owner-approved workflow.

The begin command prints the exact bounded objective to use if the owner explicitly requested Goal mode.
Run it from the Git worktree root. The guard refuses allowed paths that were already dirty when the
lease began because it cannot safely attribute those edits to the current slice.

## Verify

Run a declared command check by id:

```powershell
py -3 "C:\Users\ckvam\.codex\skills\drive-project-work\scripts\slice_guard.py" run-check --session "<session-id>" --id A1
```

Record a declared observation only after inspecting a current artifact:

```powershell
py -3 "C:\Users\ckvam\.codex\skills\drive-project-work\scripts\slice_guard.py" observe --session "<session-id>" --id A2 --note "Opened the saved project in the packaged app; the exact source and plot returned" --artifact "C:\temp\project-reopen.png"
```

An observation is recorded as `agent-observed`. It keeps the final state at `Candidate needs owner acceptance`; it cannot certify its own independent acceptance.

Ask for candidate status after every Codex-runnable check passes:

```powershell
py -3 "C:\Users\ckvam\.codex\skills\drive-project-work\scripts\slice_guard.py" candidate --session "<session-id>"
```

The candidate command compares current Git and non-noisy ignored state with the baseline, rejects any
changed path outside the lease, and requires every check and observation to match the current worktree
fingerprint. An edit after a passing check makes that evidence stale. A slice with no changed allowed
path returns a clean no-op instead of a delivery candidate.

While a lease exists, local tools fail closed: only scoped `apply_patch`, exact guard invocations, and
a small explicit read-only tool and shell allowlist run directly. Put each build, test, lint, formatter,
generator, or executable exercise in the original contract and run it through `run-check`. Git delivery
and structured write tools are outside the lease.

## Inspect, stop, or change direction

Show state without changing it:

```powershell
py -3 "C:\Users\ckvam\.codex\skills\drive-project-work\scripts\slice_guard.py" status --session "<session-id>"
```

Abort before replacing a slice whose outcome genuinely changed:

```powershell
py -3 "C:\Users\ckvam\.codex\skills\drive-project-work\scripts\slice_guard.py" abort --session "<session-id>" --reason "Owner replaced the active outcome"
```

Do not edit the machine-local state file directly. A missing or broken guard is a blocker to the guarded claim, not permission to continue without it.
If an older guard schema is found, it enters `migration_required`; use the displayed exact `abort`
command and establish a new contract instead of trusting incompatible evidence.

When `subagents` is `reviewer`, the lifecycle hooks allow one initial reviewer request, hold the shared
lease read-only from `SubagentStart` through `SubagentStop`, and reject follow-up messages or another
review pass. The reviewer does not become an acceptance authority.
