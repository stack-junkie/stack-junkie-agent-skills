# Changelog

All notable changes to the Stack Junkie Agent Skills collection are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the collection follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- Renamed Repository Management to the neutral `repo-readiness` skill identifier.

## [1.3.0] - 2026-08-19

### Added

- **Thread Steward (`manage-codex-work`) 1.0.0:** Added read-only reconciliation of recent and active Codex conversations, a concise decision inbox, local parking, relationship detection, and validation-theatre warnings without cross-chat actions.
- **Drive Project Work (`drive-project-work`) 0.2.0-alpha.0:** Added bounded delivery slices and the optional Codex lifecycle hook to the portable skill collection.
- **Repository Management (`repo-readiness`) 1.2.0:** Added concise bug and improvement issue workflows with reusable GitHub templates and verification-before-close guidance.
- **Collection:** Added one root installer and one collection-wide validation and test command for all skill packages.

### Changed

- **Collection:** Established independent SemVer sources for every skill while retaining root `VERSION` for collection snapshots.
- **Repository Management:** Consolidated repository-policy execution on the implementation shipped inside `repo-readiness`.

## [1.2.0] - 2026-08-18

### Added

- Added `preserve-compaction-continuity` with transcript-backed recovery, a visible post-compaction status report, and preview-first Codex hook management.

## [1.1.0] - 2026-08-12

### Added

- Added proportional `full`, `focused`, and `token` Stack Junkie audit tiers with separate runtime evidence for behavioral claims.
- Added bounded repository verification commands, complete policy configuration validation, and multi-remote repository health reporting.

### Fixed

- Made the Stack Junkie specimen's tabs, switch focus, narrow workbench disclosures, and persisted themes behave like the patterns they demonstrate.
- Made release metadata updates rollback safely and commit impact enforcement accept only a real, unique Git trailer.
- Stopped remote default-branch aliases such as `origin/HEAD` from appearing as stray branches in repository-health reports.

### Security

- Changed tracked secret scanning to inspect every regular Git index blob, including conflict stages and case-colliding paths, without following working-tree symlinks or traversing submodules.

## [1.0.0] - 2026-08-12

### Added

- Published `stack-junkie-style` with its visual specimen, UX references, compliance workflow, validator, and approved example screenshots.
- Published `repo-readiness` with main-first repository governance, README upkeep, release policy, local hooks, and Gitleaks enforcement.
- Established one cross-agent package layout for Codex, Claude Code, T3 Code provider harnesses, and other Agent Skills compatible clients.
