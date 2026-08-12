from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "stack-junkie-style"
VALIDATOR = SKILL / "scripts" / "validate_compliance.py"
TEMPLATE = SKILL / "assets" / "templates" / "compliance-report.md"
CHECK_LINE = re.compile(
    r"^- \[ \] (?P<id>SJ-[A-Z0-9]+-\d{2}) (?P<label>.*?) "
    r"\| Result: TODO \| Evidence: N/A \| Notes: N/A$",
    re.MULTILINE,
)


def run_validator(
    report: Path,
    *extra: str,
    expected: int = 0,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(report), *extra],
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    if result.returncode != expected:
        raise AssertionError(
            f"Expected exit {expected}, got {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def build_report(
    root: Path,
    *,
    tier: str = "full",
    audit_level: str = "independent",
    runtime_pass: bool = False,
    include_runtime: bool = False,
    legacy: bool = False,
    token_reason: str | None = None,
    create_image: bool = True,
) -> Path:
    text = TEMPLATE.read_text(encoding="utf-8")
    reason = token_reason or (
        "A primitive-only change with no layout, content, behavior, responsive, or semantic changes."
        if tier == "token"
        else "The selected tier matches one bounded and explicitly documented visual scope."
    )
    replacements = {
        "Project: TODO": "Project: Validator fixture",
        "Scope: TODO": "Scope: One documented specimen surface",
        "Date: TODO": "Date: 2026-08-12",
        "Implementer: TODO": "Implementer: Fixture implementer",
        "Audit level: TODO": f"Audit level: {audit_level}",
        "Coverage tier: TODO": f"Coverage tier: {tier}",
        "Coverage tier reason: TODO": f"Coverage tier reason: {reason}",
        "Independent verifier: TODO": (
            "Independent verifier: Fixture verifier"
            if audit_level == "independent"
            else "Independent verifier: Unavailable"
        ),
        "Independent verification: TODO": (
            "Independent verification: PASS"
            if audit_level == "independent"
            else "Independent verification: NOT RUN"
        ),
        "Theme source: TODO": "Theme source: Fixture semantic tokens",
        "Evidence directory: TODO": "Evidence directory: .",
        "| E01 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |": (
            "| E01 | evidence.png | After | Dark | Specimen | Ready | Normal | 1280x800 | Representative surface |"
        ),
        "| R01 | TODO | TODO | TODO | TODO |": (
            "| R01 | Browser automation | Explicit theme persistence | PASS | playwright theme reload assertion |"
            if include_runtime
            else ""
        ),
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    passing = {"SJ-SCOPE-03", "SJ-EVID-04"}
    if runtime_pass:
        passing.add("SJ-FOUND-09")

    def replace_check(match: re.Match[str]) -> str:
        check_id = match.group("id")
        label = match.group("label")
        if check_id in passing:
            evidence = "E01 R01" if check_id == "SJ-FOUND-09" and include_runtime else "E01"
            return (
                f"- [x] {check_id} {label} | Result: PASS | Evidence: {evidence} "
                "| Notes: Verified by the cited fixture evidence."
            )
        return (
            f"- [x] {check_id} {label} | Result: N/A | Evidence: N/A "
            "| Notes: This dimension is outside the deliberately bounded fixture scope."
        )

    text = CHECK_LINE.sub(replace_check, text)
    if legacy:
        text = re.sub(r"^Coverage tier:.*\n", "", text, flags=re.MULTILINE)
        text = re.sub(r"^Coverage tier reason:.*\n", "", text, flags=re.MULTILINE)
        text = re.sub(r"^- \[x\] SJ-FOUND-09 .*\n", "", text, flags=re.MULTILINE)
    text = text.replace("TODO", "Documented fixture detail")

    report = root / "report.md"
    report.write_text(text, encoding="utf-8", newline="\n")
    if create_image:
        (root / "evidence.png").write_bytes(b"fixture image")
    return report


class ComplianceValidatorTests(unittest.TestCase):
    def test_all_coverage_tiers_and_legacy_default(self) -> None:
        for tier in ("full", "focused", "token"):
            with self.subTest(tier=tier), tempfile.TemporaryDirectory() as temp:
                report = build_report(Path(temp), tier=tier)
                result = run_validator(report, "--coverage-tier", tier)
                self.assertIn(f"Coverage tier: {tier}", result.stdout)

        with tempfile.TemporaryDirectory() as temp:
            report = build_report(Path(temp), legacy=True)
            result = run_validator(report)
            self.assertIn("Coverage tier: full", result.stdout)

    def test_token_tier_requires_explicit_no_change_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            report = build_report(
                Path(temp), tier="token", token_reason="Only a small visual adjustment was made."
            )
            result = run_validator(report, "--coverage-tier", "token", expected=1)
            self.assertIn("Token coverage requires the explicit attestation", result.stdout)

    def test_runtime_evidence_is_required_and_must_be_referenced(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            report = build_report(Path(temp), runtime_pass=True)
            result = run_validator(report, expected=1)
            self.assertIn("requires runtime evidence in addition to screenshots", result.stdout)

        with tempfile.TemporaryDirectory() as temp:
            report = build_report(Path(temp), runtime_pass=True, include_runtime=True)
            run_validator(report)

        with tempfile.TemporaryDirectory() as temp:
            report = build_report(Path(temp), include_runtime=True)
            result = run_validator(report, expected=1)
            self.assertIn("runtime evidence is not cited", result.stdout)

    def test_visual_pass_requires_an_existing_screenshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            report = build_report(Path(temp), create_image=False)
            result = run_validator(report, expected=1)
            self.assertIn("evidence image does not exist", result.stdout)

    def test_independent_and_self_audit_claims_remain_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            report = build_report(Path(temp), audit_level="self")
            result = run_validator(report, "--audit-level", "self")
            self.assertIn("Claim ceiling: Implemented and self-audited", result.stdout)

        with tempfile.TemporaryDirectory() as temp:
            report = build_report(Path(temp), audit_level="self")
            result = run_validator(report, expected=1)
            self.assertIn("report Audit level is 'self'", result.stdout)


if __name__ == "__main__":
    unittest.main()
