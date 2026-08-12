# Changelog

All notable changes to the Stack Junkie Agent Skills collection are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the collection follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
