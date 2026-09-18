# Interactive GUI validation loop

Use this pattern when a focused issue can compile cleanly but correctness depends on mouse, keyboard, timing, drag/drop, or visual state.

## Validation loop

1. Keep each issue on its own branch and combine approved commits only on a disposable local integration branch.
2. Build and install the integration branch to an unmistakably isolated path. Launch that exact executable, not an older installed copy.
3. Tell the owner precisely which fixes are in the running binary and give a short behavior-first checklist.
4. Treat the owner's direct workflow result as the publication gate:
   - **Pass:** publish the focused issue branch/PR with the owner-run workflow recorded as evidence.
   - **Fail:** do not publish that issue yet. Capture the exact gesture sequence and observed state transition, return the correction to the same issue branch, review it, incrementally rebuild the integration binary, and retest.
5. Keep already-passing, disjoint issues moving; one failed GUI issue should not block unrelated reviewed branches.
6. Once the bug passes, separate newly requested polish or redesign into follow-up enhancement work.

## Timing-sensitive drag/drop lesson

Signals emitted during a gesture may represent intermediate motion, not final intent. For example, Qt `QTabBar::tabMoved` can fire repeatedly as a dragged tab crosses neighbors. Mutating durable group membership on every signal can steal or split groups merely on hover/crossing.

For this class of interaction:

- preserve the identity of the object captured at mouse press;
- update transient visual order/preview during motion;
- defer durable membership changes until release/drop;
- support cancel/lost-focus cleanup;
- keep programmatic moves on an explicit non-drag path;
- test crossing without dropping, boundary drops, same-group reorder, outside-group removal, and valid target insertion.

## Communication

When the owner is waiting on a long build, status should be terse and concrete: `still running, 530/862, no errors`. Do not repeat the plan or restart permission discussion after the intrusive action was already explicitly authorized. If the owner reports an unexpected intrusion, stop only that intrusive activity first and state exactly what did and did not complete.