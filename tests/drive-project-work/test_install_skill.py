from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts" / "install_skill.ps1"


class InstallSkillTests(unittest.TestCase):
    def test_drive_skill_and_hook_install_into_temporary_codex_home(self) -> None:
        powershell = shutil.which("powershell") or shutil.which("pwsh")
        if not powershell:
            self.skipTest("PowerShell is not available")
        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary) / "codex"
            skills_dir = codex_home / "skills"
            command = [
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(INSTALLER),
                "-Name",
                "drive-project-work",
                "-SkillsDir",
                str(skills_dir),
                "-InstallCodexHook",
            ]
            first = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, encoding="utf-8")
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            second = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, encoding="utf-8")
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertTrue((skills_dir / "drive-project-work" / "SKILL.md").is_file())
            self.assertTrue((codex_home / "hooks" / "drive_project_work_hook.py").is_file())
            self.assertTrue((codex_home / "hooks.json").is_file())


if __name__ == "__main__":
    unittest.main()
