from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "manage-codex-work"
    / "scripts"
    / "thread_steward.py"
)
SPEC = importlib.util.spec_from_file_location("thread_steward", MODULE_PATH)
assert SPEC and SPEC.loader
thread_steward = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(thread_steward)


def thread(
    thread_id: str,
    *,
    cwd: str = "C:/work/project",
    preview: str = "Build the requested feature",
    user: str = "Please implement the feature",
    agent: str = "Implemented the feature.",
    status: str = "completed",
    name: str | None = None,
) -> dict[str, object]:
    return {
        "id": thread_id,
        "name": name,
        "preview": preview,
        "cwd": cwd,
        "createdAt": 1_787_000_000,
        "updatedAt": 1_787_000_100,
        "recencyAt": 1_787_000_100,
        "source": "vscode",
        "status": {"type": "notLoaded"},
        "parentThreadId": None,
        "forkedFromId": None,
        "turns": [
            {
                "status": status,
                "items": [
                    {"type": "userMessage", "content": user},
                    {"type": "agentMessage", "content": agent},
                ],
            }
        ],
    }


class ThreadStewardTests(unittest.TestCase):
    def test_runtime_version_matches_the_skill_package(self) -> None:
        self.assertEqual(thread_steward.package_version(), "1.0.0")

    def test_current_invoking_thread_is_not_classified_as_needing_owner_input(self) -> None:
        thread_id = "00000000-0000-0000-0000-000000000001"
        sample = thread(thread_id, status="interrupted")
        prepared = thread_steward.prepare_thread(
            sample,
            thread_steward.new_state(),
            "review-1",
            thread_steward.parse_time("2026-08-19T12:00:00Z"),
            set(),
            thread_id,
        )
        self.assertTrue(prepared["is_current"])
        self.assertEqual(prepared["suggested_category"], "current")

    def test_visible_completion_without_observation_is_at_risk(self) -> None:
        sample = thread(
            "00000000-0000-0000-0000-000000000001",
            user="Make the browser tab group appearance match the real UI.",
            agent="Implemented it and all tests passed. I also created a validation framework.",
        )
        prepared = thread_steward.prepare_thread(
            sample,
            thread_steward.new_state(),
            "review-1",
            thread_steward.parse_time("2026-08-19T12:00:00Z"),
            set(),
        )
        self.assertEqual(prepared["suggested_category"], "at_risk")
        self.assertTrue(any("direct" in signal for signal in prepared["risk_signals"]))

    def test_filing_a_ui_issue_is_not_treated_as_claiming_the_ui_is_complete(self) -> None:
        sample = thread(
            "00000000-0000-0000-0000-000000000001",
            user="Add an issue to simplify the waveform analysis UI.",
            agent="Added issue #11 for the UI pass. Local files were untouched.",
        )
        sample["turns"].insert(
            0,
            {
                "status": "completed",
                "items": [
                    {"type": "userMessage", "content": "Implement an unrelated feature."},
                    {"type": "agentMessage", "content": "Implemented it and completed the tests."},
                ],
            },
        )
        prepared = thread_steward.prepare_thread(
            sample,
            thread_steward.new_state(),
            "review-1",
            thread_steward.parse_time("2026-08-19T12:00:00Z"),
            set(),
        )
        self.assertNotEqual(prepared["suggested_category"], "at_risk")

    def test_historical_validation_theater_audit_is_not_a_current_risk(self) -> None:
        sample = thread(
            "00000000-0000-0000-0000-000000000001",
            user="Apply the backlog cleanup we just agreed on.",
            agent="Done. The backlog cleanup is applied.",
        )
        sample["turns"].insert(
            0,
            {
                "status": "completed",
                "items": [
                    {
                        "type": "userMessage",
                        "content": "Add an issue to audit tests for validation theatre.",
                    },
                    {"type": "agentMessage", "content": "Added the audit issue."},
                ],
            },
        )
        prepared = thread_steward.prepare_thread(
            sample,
            thread_steward.new_state(),
            "review-1",
            thread_steward.parse_time("2026-08-19T12:00:00Z"),
            set(),
        )
        self.assertNotEqual(prepared["suggested_category"], "at_risk")

    def test_same_repository_alone_does_not_create_relationship(self) -> None:
        first = thread_steward.prepare_thread(
            thread(
                "00000000-0000-0000-0000-000000000001",
                preview="Repair EtherCAT RollCall decoding issue #8",
                user="Fix RollCall decoding for frame zero",
            ),
            thread_steward.new_state(),
            "review-1",
            thread_steward.parse_time("2026-08-19T12:00:00Z"),
            set(),
        )
        second = thread_steward.prepare_thread(
            thread(
                "00000000-0000-0000-0000-000000000002",
                preview="Redesign browser-style tab groups",
                user="Make tab groups visually clearer",
            ),
            thread_steward.new_state(),
            "review-1",
            thread_steward.parse_time("2026-08-19T12:00:00Z"),
            set(),
        )
        self.assertEqual(
            thread_steward.relationship_candidates([first, second], thread_steward.new_state()), []
        )

    def test_shared_issue_identifier_creates_strong_candidate(self) -> None:
        left = thread_steward.prepare_thread(
            thread(
                "00000000-0000-0000-0000-000000000001",
                preview="Investigate EtherCAT parity issue #10",
                user="Find the previous chat about issue #10",
            ),
            thread_steward.new_state(), "review-1",
            thread_steward.parse_time("2026-08-19T12:00:00Z"), set(),
        )
        right = thread_steward.prepare_thread(
            thread(
                "00000000-0000-0000-0000-000000000002",
                preview="Finish implementation from issue #10",
                user="Take over the existing EtherCAT work for #10",
            ),
            thread_steward.new_state(), "review-1",
            thread_steward.parse_time("2026-08-19T12:00:00Z"), set(),
        )
        candidates = thread_steward.relationship_candidates([left, right], thread_steward.new_state())
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["confidence"], "strong")

    def test_generic_skill_filename_is_not_relationship_evidence(self) -> None:
        left = thread_steward.prepare_thread(
            thread(
                "00000000-0000-0000-0000-000000000001",
                cwd="C:/work/one",
                preview="Create a PDF skill",
                user="Update SKILL.md for PDF rotation",
            ),
            thread_steward.new_state(), "review-1",
            thread_steward.parse_time("2026-08-19T12:00:00Z"), set(),
        )
        right = thread_steward.prepare_thread(
            thread(
                "00000000-0000-0000-0000-000000000002",
                cwd="C:/work/two",
                preview="Create a calendar skill",
                user="Update SKILL.md for calendar review",
            ),
            thread_steward.new_state(), "review-1",
            thread_steward.parse_time("2026-08-19T12:00:00Z"), set(),
        )
        self.assertEqual(
            thread_steward.relationship_candidates([left, right], thread_steward.new_state()), []
        )

    def test_explicit_thread_id_reference_is_strong_relationship_evidence(self) -> None:
        first_id = "00000000-0000-0000-0000-000000000001"
        second_id = "00000000-0000-0000-0000-000000000002"
        left = thread_steward.prepare_thread(
            thread(first_id, cwd="C:/work/one", preview="Coordinator design"),
            thread_steward.new_state(), "review-1",
            thread_steward.parse_time("2026-08-19T12:00:00Z"), set(),
        )
        right = thread_steward.prepare_thread(
            thread(second_id, cwd="C:/work/two", agent=f"The correct coordinator is thread {first_id}."),
            thread_steward.new_state(), "review-1",
            thread_steward.parse_time("2026-08-19T12:00:00Z"), set(),
        )
        candidates = thread_steward.relationship_candidates([left, right], thread_steward.new_state())
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["confidence"], "strong")

    def test_parking_resurfaces_on_next_review_and_close_preserves_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "state.json"
            store = thread_steward.StateStore(state_path)
            state = thread_steward.new_state()
            state["last_review_id"] = "review-1"
            state["workstreams"]["tabs"] = {
                "title": "Tab groups",
                "canonical_thread_id": "00000000-0000-0000-0000-000000000001",
                "related_thread_ids": [],
                "status": "parked",
                "park": {
                    "trigger_type": "next_review",
                    "trigger_value": None,
                    "parked_at_review": "review-1",
                },
            }
            store.save(state)
            loaded = store.load()
            self.assertEqual(
                thread_steward.workstream_state_for_thread(
                    "00000000-0000-0000-0000-000000000001",
                    loaded,
                    "review-2",
                    thread_steward.parse_time("2026-08-19T12:00:00Z"),
                ),
                "due_to_resurface",
            )
            args = mock.Mock(state_file=str(state_path), workstream_id="tabs")
            with mock.patch("builtins.print"):
                self.assertEqual(thread_steward.state_change_status(args, "closed"), 0)
            closed = store.load()
            self.assertIn("tabs", closed["workstreams"])
            self.assertEqual(closed["workstreams"]["tabs"]["status"], "closed")

    def test_state_write_is_valid_and_does_not_store_transcripts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            store = thread_steward.StateStore(path)
            state = thread_steward.new_state()
            state["workstreams"]["coordinator"] = {
                "title": "Thread Steward",
                "canonical_thread_id": "00000000-0000-0000-0000-000000000001",
                "related_thread_ids": [],
                "status": "active",
            }
            store.save(state)
            encoded = path.read_text(encoding="utf-8")
            self.assertEqual(json.loads(encoded)["schema_version"], 1)
            self.assertNotIn("messages", encoded)
            self.assertFalse(any(path.parent.glob("*.tmp")))

    def test_relate_adds_threads_without_discarding_existing_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "state.json"
            store = thread_steward.StateStore(state_path)
            state = thread_steward.new_state()
            state["workstreams"]["coordinator"] = {
                "title": "Thread Steward",
                "canonical_thread_id": "00000000-0000-0000-0000-000000000001",
                "related_thread_ids": ["00000000-0000-0000-0000-000000000002"],
                "status": "active",
            }
            store.save(state)
            args = mock.Mock(
                state_file=str(state_path),
                workstream_id="coordinator",
                title="Thread Steward",
                canonical="00000000-0000-0000-0000-000000000001",
                related=["00000000-0000-0000-0000-000000000003"],
            )
            with mock.patch("builtins.print"):
                self.assertEqual(thread_steward.state_relate(args), 0)
            related = store.load()["workstreams"]["coordinator"]["related_thread_ids"]
            self.assertEqual(
                related,
                [
                    "00000000-0000-0000-0000-000000000002",
                    "00000000-0000-0000-0000-000000000003",
                ],
            )

    def test_read_only_release_contains_no_cross_thread_action_methods(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        for forbidden in ("turn/start", "turn/steer", "turn/interrupt", "thread/archive", "thread/unarchive"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
