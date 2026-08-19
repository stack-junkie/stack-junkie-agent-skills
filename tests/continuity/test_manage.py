from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "preserve-compaction-continuity"
    / "scripts"
    / "manage.py"
)
SPEC = importlib.util.spec_from_file_location("continuity_manage", MODULE_PATH)
assert SPEC and SPEC.loader
manage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage)


def stale_hooks() -> dict[str, object]:
    return {
        "description": "Existing user hooks",
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "shell",
                    "hooks": [{"type": "command", "command": "keep-me"}],
                }
            ],
            "PreCompact": [
                {
                    "matcher": "manual|auto",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python3 /old/continuity_recovery.py",
                            "statusMessage": "Preserving the full recovery packet",
                        }
                    ],
                }
            ],
        },
    }


class ContinuityManagerTests(unittest.TestCase):
    def test_preview_is_read_only_then_install_is_current_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "codex"
            home.mkdir()
            hooks_path = home / "hooks.json"
            original = json.dumps(stale_hooks(), indent=2) + "\n"
            hooks_path.write_text(original, encoding="utf-8")
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(home)}):
                self.assertEqual(manage.install(False), 0)
                self.assertEqual(hooks_path.read_text(encoding="utf-8"), original)
                self.assertFalse((home / "skills" / manage.SKILL_NAME).exists())
                self.assertEqual(manage.install(True), 0)
                first_backups = sorted(
                    path.relative_to(home) for path in (home / "backups" / manage.SKILL_NAME).rglob("*")
                )
                self.assertEqual(manage.status(), 0)
                self.assertEqual(manage.install(True), 0)
                second_backups = sorted(
                    path.relative_to(home) for path in (home / "backups" / manage.SKILL_NAME).rglob("*")
                )
            self.assertEqual(first_backups, second_backups)
            installed = json.loads(hooks_path.read_text(encoding="utf-8"))
            self.assertEqual(installed["description"], "Existing user hooks")
            self.assertEqual(
                installed["hooks"]["PreToolUse"][0]["hooks"][0]["command"],
                "keep-me",
            )
            self.assertEqual(len(installed["hooks"]["PreCompact"]), 1)
            self.assertEqual(len(installed["hooks"]["SessionStart"]), 1)
            self.assertTrue((home / "hooks" / "continuity_recovery.py").is_file())
            self.assertTrue((home / "skills" / manage.SKILL_NAME / "SKILL.md").is_file())

    def test_install_status_uninstall_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "codex"
            home.mkdir()
            (home / "hooks.json").write_text(
                json.dumps(stale_hooks(), indent=2) + "\n", encoding="utf-8"
            )
            packet = home / "continuity" / "session" / "recovery.md"
            packet.parent.mkdir(parents=True)
            packet.write_text("private packet", encoding="utf-8")
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(home)}):
                self.assertEqual(manage.install(True), 0)
                self.assertEqual(manage.status(), 0)
                before = (home / "hooks.json").read_text(encoding="utf-8")
                self.assertEqual(manage.uninstall(False), 0)
                self.assertEqual((home / "hooks.json").read_text(encoding="utf-8"), before)
                self.assertEqual(manage.uninstall(True), 0)
            remaining = json.loads((home / "hooks.json").read_text(encoding="utf-8"))
            self.assertIn("PreToolUse", remaining["hooks"])
            self.assertNotIn("PreCompact", remaining["hooks"])
            self.assertNotIn("SessionStart", remaining["hooks"])
            self.assertFalse((home / "hooks" / "continuity_recovery.py").exists())
            self.assertFalse((home / "skills" / manage.SKILL_NAME).exists())
            self.assertEqual(packet.read_text(encoding="utf-8"), "private packet")

    def test_status_prints_only_installation_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "codex"
            home.mkdir()
            secret = "private prompt must not print"
            packet = home / "continuity" / "session" / "recovery.md"
            packet.parent.mkdir(parents=True)
            packet.write_text(secret, encoding="utf-8")
            output = StringIO()
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(home)}), redirect_stdout(output):
                self.assertEqual(manage.status(), 1)
            self.assertNotIn(secret, output.getvalue())


if __name__ == "__main__":
    unittest.main()
