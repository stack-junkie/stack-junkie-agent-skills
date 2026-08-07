# Changelog

All notable changes to the maintained `drive-project-work` skill are documented here.

## [0.2.0-alpha.0] - 2026-08-06

### Changed

- Replaced the broad self-scored project controller with a single-purpose bounded-slice workflow.
- Limited completion language to locally verified candidate states and explicit remaining owner gates.
- Removed EtherPlot-specific delivery, release, communication, and process-deviation rules from the skill.

### Added

- Added a machine-local slice lease with one outcome, one to five predeclared checks, allowed paths,
  outside-scope items, and optional bounded reviewer authority.
- Added lifecycle hooks that block out-of-scope patches, undeclared verification, premature Goal
  completion, subagent fan-out, work after an owner stop, and inflated final claims.
- Added executable checks for contract bounds, stop-latch behavior, Goal matching, scope-diff
  enforcement, candidate claims, and idempotent hook installation.
- Bound guard commands to the installed script, active session, exact arguments, and repository root;
  unclassified command-carrying tools now fail closed while a lease exists.
- Added evidence-freshness fingerprints, pre-existing dirty-path rejection, full non-noisy ignored-file
  comparison, and a lifecycle-enforced read-only reviewer latch.
- Default-denied unclassified structured local tools during a lease and moved Goal creation and
  completion state to successful `PostToolUse` confirmation.
- Added fail-closed recovery for older machine-local guard schemas and broader literal owner-stop forms.
- Corrected the Windows Python launcher so a failing validator or test suite returns a failing process
  status instead of being misreported as successful.

## [0.1.0-alpha.4] - 2026-08-06

### Changed

- Required ordinary English before technical terms, with immediate plain-language definitions and
  concrete examples whenever jargon is genuinely necessary.

## [0.1.0-alpha.3] - 2026-08-06

### Changed

- Added the owner's standing communication preference: blunt and correctly spelled, no em dashes,
  occasional useful profanity, no forced repetition, and direct non-hateful alternatives to racial
  slurs.

## [0.1.0-alpha.2] - 2026-08-06

### Changed

- Added the EtherPlot per-slice delivery cadence: verified versioned checkpoints, authorized branch
  pushes, immediate chat and self-email test instructions, inspected screenshots for visual work,
  and a final README plus stale-documentation reconciliation slice.

## [0.1.0-alpha.1] - 2026-08-05

### Changed

- Added an objective 14-check intent rubric requiring at least 13 clear checks and no unresolved critical product-intent checks before implementation.
- Required targeted clarification rounds without stalling unrelated work whose intent is already clear.

## [0.1.0-alpha.0] - 2026-08-04

### Added

- Added the project-driving workflow from request intake through verified checkpoint.
- Added owner-decision extraction with recommendations and explicit reasoning.
- Added preference-deviation detection that distinguishes task-only exceptions from future process changes.
- Added a maintained-source update, validation, reinstall, and comparison workflow.
- Added release classification, verification levels, and a read-only project inspection script.
