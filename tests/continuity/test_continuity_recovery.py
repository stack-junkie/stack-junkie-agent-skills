from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "preserve-compaction-continuity"
    / "scripts"
    / "continuity_recovery.py"
)
SPEC = importlib.util.spec_from_file_location("continuity_recovery", MODULE_PATH)
assert SPEC and SPEC.loader
continuity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(continuity)


def message(role: str, text: str) -> dict[str, object]:
    return {
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": role,
            "content": [{"type": "input_text", "text": text}],
        },
    }


def write_transcript(path: Path, user_count: int = 10) -> None:
    records: list[dict[str, object]] = [
        message(
            "user",
            "<recommended_plugins>generated</recommended_plugins>\n"
            "<environment_context>generated</environment_context>",
        )
    ]
    for index in range(user_count):
        records.append(message("user", f"Exact request {index} →"))
        records.append(message("assistant", f"Work update {index}."))
    records.extend(
        [
            {"type": "turn_context", "payload": {"summary": "Current task summary."}},
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "last_token_usage": {"input_tokens": 778},
                        "model_context_window": 1000,
                    },
                },
            },
        ]
    )
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )


class ContinuityHookTests(unittest.TestCase):
    def snapshot(self, root: Path, trigger: str = "auto") -> dict[str, object]:
        transcript = root / "rollout.jsonl"
        write_transcript(transcript)
        return continuity.handle(
            {
                "session_id": "session-test",
                "turn_id": "turn-test",
                "transcript_path": str(transcript),
                "cwd": str(root),
                "hook_event_name": "PreCompact",
                "trigger": trigger,
                "model": "test-model",
            }
        )

    def test_compact_injects_verified_visible_report_and_exact_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "continuity"
            with mock.patch.dict(os.environ, {"CODEX_CONTINUITY_HOME": str(output)}):
                result = self.snapshot(root)
                resumed = continuity.handle(
                    {
                        "session_id": "session-test",
                        "hook_event_name": "SessionStart",
                        "source": "compact",
                    }
                )
            self.assertTrue(result["continue"])
            packet = (output / "session-test" / "recovery.md").read_text(encoding="utf-8")
            manifest = json.loads(
                (output / "session-test" / "manifest.json").read_text(encoding="utf-8")
            )
            context = resumed["hookSpecificOutput"]["additionalContext"]
            self.assertEqual(manifest["user_prompt_count"], 10)
            self.assertEqual(manifest["conversation_message_count"], 20)
            self.assertEqual(manifest["preservation"]["injected_user_prompt_count"], 8)
            self.assertEqual(manifest["preservation"]["injected_conversation_message_count"], 6)
            self.assertIn("Exact request 0 →", packet)
            self.assertIn("Exact request 9 →", packet)
            self.assertNotIn("<recommended_plugins>", packet)
            self.assertIn("### Context recovery", context)
            self.assertIn("Automatic at 77.8%", context)
            self.assertIn("all 10 user prompts", context)
            self.assertIn("8 latest user prompts plus 6 of 20", context)
            self.assertIn("Before any tool call", context)

    def test_manual_compaction_uses_manual_reason(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with mock.patch.dict(os.environ, {"CODEX_CONTINUITY_HOME": str(root / "out")}):
                self.snapshot(root, trigger="manual")
                resumed = continuity.handle(
                    {
                        "session_id": "session-test",
                        "hook_event_name": "SessionStart",
                        "source": "compact",
                    }
                )
            context = resumed["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Compaction: Manual", context)
            self.assertIn("Manual compaction was requested", context)

    def test_ordinary_resume_restores_evidence_without_compaction_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with mock.patch.dict(os.environ, {"CODEX_CONTINUITY_HOME": str(root / "out")}):
                self.snapshot(root)
                resumed = continuity.handle(
                    {
                        "session_id": "session-test",
                        "hook_event_name": "SessionStart",
                        "source": "resume",
                    }
                )
            context = resumed["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Mandatory post-compaction recovery context", context)
            self.assertNotIn("Mandatory visible compaction report", context)

    def test_corrupt_handoff_reports_failure_instead_of_success(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "out"
            with mock.patch.dict(os.environ, {"CODEX_CONTINUITY_HOME": str(output)}):
                self.snapshot(root)
                (output / "session-test" / "rehydrate.md").write_text(
                    "corrupt", encoding="utf-8"
                )
                resumed = continuity.handle(
                    {
                        "session_id": "session-test",
                        "hook_event_name": "SessionStart",
                        "source": "compact",
                    }
                )
            self.assertNotIn("hookSpecificOutput", resumed)
            self.assertIn("failed", resumed["systemMessage"])
            self.assertNotIn("Successful", resumed["systemMessage"])

    def test_precompact_fails_closed_without_transcript(self) -> None:
        result = continuity.handle(
            {
                "session_id": "session-test",
                "hook_event_name": "PreCompact",
                "trigger": "manual",
            }
        )
        self.assertFalse(result["continue"])
        self.assertIn("snapshot failed", result["stopReason"])

    def test_cli_emits_utf8_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "out"
            with mock.patch.dict(os.environ, {"CODEX_CONTINUITY_HOME": str(output)}):
                self.snapshot(root)
            environment = os.environ.copy()
            environment["CODEX_CONTINUITY_HOME"] = str(output)
            completed = subprocess.run(
                [sys.executable, str(MODULE_PATH)],
                input=json.dumps(
                    {
                        "session_id": "session-test",
                        "hook_event_name": "SessionStart",
                        "source": "compact",
                    }
                ).encode("utf-8"),
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8"))
            parsed = json.loads(completed.stdout.decode("utf-8"))
            self.assertIn("Exact request 9 →", parsed["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
