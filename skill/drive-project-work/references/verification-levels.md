# Verification levels

Choose the highest level required by the claimed outcome. Passing a lower level does not prove a higher-level claim.

## V0: Inspection

Use for diagnosis, audits, planning, and orientation.

Evidence may include source tracing, live state, logs, reproduction results, dependency identity, and current configuration. V0 supports conclusions and plans, not implementation claims.

## V1: Focused

Use while implementing a bounded change.

Examples include syntax checks, lint, type checks, unit tests, a narrow regression test, metadata validation, or a focused component probe.

## V2: Integrated

Use when the change participates in a larger application or package.

Run the relevant suite and production build. Verify that integration, generated artifacts, and public contracts remain coherent. A build alone does not prove user behavior.

## V3: Exercised

Use for claims about a real workflow.

Start the production application or service and exercise the affected path with representative inputs. Observe the expected output and relevant failure states. Prefer a before-and-after reproduction for defects.

## V4: Product

Use for visual, packaged, installed, persistence, migration, or lifecycle claims.

Examples include direct screenshot inspection at a representative state, packaged executable smoke tests, installation and launcher checks, save/reopen round trips, upgrade/rollback exercises, accessibility checks, and cancellation/recovery behavior.

## V5: Release

Use for release-ready, distribution-ready, or supported-platform claims.

Include the declared clean-machine and platform matrix, signing, licensing, packaging, installer/uninstaller lifecycle, upgrade and rollback, distribution rules, and owner approvals. Report every unavailable gate. Local tests and packaging do not establish V5.

## Reporting

For every completed task, state:

- the highest level reached;
- the exact commands or interactions performed;
- the observed result;
- skipped or unavailable checks;
- why the evidence is sufficient for the narrow claim being made.

Do not inflate a V1 or V2 result into a V3 through V5 claim.
