from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
GUARD_PATH = REPO_ROOT / "skill" / "drive-project-work" / "scripts" / "slice_guard.py"
INSTALL_HOOKS_PATH = REPO_ROOT / "scripts" / "install_hooks.py"
HOOK_ADAPTER_PATH = REPO_ROOT / "hooks" / "drive_project_work_hook.py"

spec = importlib.util.spec_from_file_location("slice_guard", GUARD_PATH)
assert spec and spec.loader
slice_guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(slice_guard)


class SliceGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.codex_home = self.root / "codex"
        self.project = self.root / "project"
        (self.project / "src").mkdir(parents=True)
        (self.project / "docs").mkdir()
        (self.project / "src" / "tracked.txt").write_text("baseline\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        subprocess.run(["git", "-C", str(self.project), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(self.project), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(self.project), "add", "src/tracked.txt"], check=True)
        subprocess.run(["git", "-C", str(self.project), "commit", "-qm", "baseline"], check=True)
        self.previous_codex_home = os.environ.get("CODEX_HOME")
        os.environ["CODEX_HOME"] = str(self.codex_home)

    def tearDown(self) -> None:
        if self.previous_codex_home is None:
            os.environ.pop("CODEX_HOME", None)
        else:
            os.environ["CODEX_HOME"] = self.previous_codex_home
        self.temporary.cleanup()

    def contract(self, **changes: object) -> dict[str, object]:
        value: dict[str, object] = {
            "outcome": "The saved document reopens with its selected source",
            "allowed_paths": ["src/tracked.txt"],
            "acceptance": [
                {
                    "id": "A1",
                    "kind": "command",
                    "criterion": "The focused reopen check passes",
                    "command": "Write-Output focused-pass",
                }
            ],
            "outside_scope": ["Release publication"],
            "subagents": "none",
        }
        value.update(changes)
        return value

    def call(self, function, *args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = function(*args)
        return result, stdout.getvalue(), stderr.getvalue()

    def begin(self, session: str = "session-one", contract: dict[str, object] | None = None) -> dict[str, object]:
        args = type("Args", (), {
            "session": session,
            "cwd": str(self.project),
            "contract": json.dumps(contract or self.contract()),
        })()
        result, output, _ = self.call(slice_guard.begin, args)
        self.assertEqual(result, 0)
        return json.loads(output)

    def test_broad_project_outcome_is_rejected(self) -> None:
        broad = self.contract(outcome="Complete the entire project backlog and all requirements")
        with self.assertRaisesRegex(slice_guard.GuardError, "broad project objective"):
            slice_guard.validate_contract(broad, self.project)

    def test_known_broad_counterexamples_are_rejected(self) -> None:
        outcomes = [
            "Improve every screen in the application",
            "Fix every defect in the application",
            "Implement ARTL, Robot, EtherCAT, Golden, waveform, measurements, annotations, and project persistence",
            "Build a production-ready app",
            "Deliver the dashboard, importer, and export workflow",
        ]
        for outcome in outcomes:
            with self.subTest(outcome=outcome):
                with self.assertRaisesRegex(slice_guard.GuardError, "(?:broad project objective|list of journeys)"):
                    slice_guard.validate_contract(self.contract(outcome=outcome), self.project)

    def test_contract_required_stub_can_be_replaced_by_bounded_slice(self) -> None:
        payload = {
            "session_id": "stub-session",
            "cwd": str(self.project),
            "hook_event_name": "UserPromptSubmit",
            "prompt": "Implement this project feature",
        }
        self.call(slice_guard.user_prompt_submit, payload, None)
        self.assertEqual(slice_guard.load_state("stub-session")["status"], "contract_required")
        self.begin("stub-session")
        self.assertEqual(slice_guard.load_state("stub-session")["status"], "active")

    def test_current_stop_phrase_does_not_trigger_owner_stop(self) -> None:
        payload = {
            "session_id": "wording-session",
            "cwd": str(self.project),
            "hook_event_name": "UserPromptSubmit",
            "prompt": "How can we stop this from happening?",
        }
        self.call(slice_guard.user_prompt_submit, payload, None)
        self.assertIsNone(slice_guard.load_state("wording-session"))

    def test_explicit_stop_latches_tools_until_explicit_resume(self) -> None:
        self.begin("stop-session")
        state = slice_guard.load_state("stop-session")
        stop_payload = {
            "session_id": "stop-session",
            "cwd": str(self.project),
            "hook_event_name": "UserPromptSubmit",
            "prompt": "Please stop working now",
        }
        self.call(slice_guard.user_prompt_submit, stop_payload, state)
        paused = slice_guard.load_state("stop-session")
        self.assertEqual(paused["status"], "paused")
        tool_payload = {
            "session_id": "stop-session",
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {"command": "*** Update File: src/tracked.txt"},
        }
        _, denied, _ = self.call(slice_guard.pre_tool_use, tool_payload, paused)
        self.assertEqual(json.loads(denied)["hookSpecificOutput"]["permissionDecision"], "deny")
        resume_payload = dict(stop_payload, prompt="Continue with the same slice")
        self.call(slice_guard.user_prompt_submit, resume_payload, paused)
        self.assertEqual(slice_guard.load_state("stop-session")["status"], "active")

    def test_normal_stop_variants_latch_and_new_instruction_does_not_resume(self) -> None:
        for index, prompt in enumerate((
            "Stop there.",
            "Don't continue working.",
            "Stop this task.",
            "Stop the current work.",
            "Stop doing that.",
            "Don't touch anything else.",
            "Please pause the task.",
            "Stop working on this project.",
            "Stop the task now.",
            "Do not make any more changes.",
            "Don't make further changes.",
        ), start=1):
            session = f"stop-variant-{index}"
            self.begin(session)
            payload = {
                "session_id": session,
                "cwd": str(self.project),
                "hook_event_name": "UserPromptSubmit",
                "prompt": prompt,
            }
            self.call(slice_guard.user_prompt_submit, payload, slice_guard.load_state(session))
            self.assertEqual(slice_guard.load_state(session)["status"], "paused")
            payload["prompt"] = "New instruction: explain the status"
            self.call(slice_guard.user_prompt_submit, payload, slice_guard.load_state(session))
            self.assertEqual(slice_guard.load_state(session)["status"], "paused")

    def test_goal_must_match_generated_candidate_boundary(self) -> None:
        self.begin("goal-session")
        state = slice_guard.load_state("goal-session")
        bad = {
            "hook_event_name": "PreToolUse",
            "tool_name": "create_goal",
            "tool_input": {"objective": "Complete the entire project backlog"},
        }
        _, denied, _ = self.call(slice_guard.pre_tool_use, bad, state)
        self.assertEqual(json.loads(denied)["hookSpecificOutput"]["permissionDecision"], "deny")
        good = dict(bad)
        good["tool_input"] = {"objective": slice_guard.goal_objective(state)}
        good["tool_use_id"] = "goal-exact-1"
        _, allowed, _ = self.call(slice_guard.pre_tool_use, good, state)
        self.assertEqual(allowed, "")

    def test_goal_state_changes_only_after_successful_post_tool_confirmation(self) -> None:
        self.begin("goal-post-session")
        state = slice_guard.load_state("goal-post-session")
        create = {
            "hook_event_name": "PreToolUse",
            "tool_name": "create_goal",
            "tool_use_id": "goal-create-1",
            "tool_input": {"objective": slice_guard.goal_objective(state)},
        }
        self.call(slice_guard.pre_tool_use, create, state)
        failed_post = {
            **create,
            "hook_event_name": "PostToolUse",
            "tool_response": {"isError": True, "error": "existing goal"},
        }
        self.call(slice_guard.post_tool_use, failed_post, slice_guard.load_state("goal-post-session"))
        self.assertFalse(slice_guard.load_state("goal-post-session")["goal_requested"])

        create["tool_use_id"] = "goal-create-denied"
        self.call(slice_guard.pre_tool_use, create, slice_guard.load_state("goal-post-session"))
        denied_post = {**create, "hook_event_name": "PostToolUse", "tool_response": {"status": "denied"}}
        self.call(slice_guard.post_tool_use, denied_post, slice_guard.load_state("goal-post-session"))
        self.assertFalse(slice_guard.load_state("goal-post-session")["goal_requested"])

        create["tool_use_id"] = "goal-create-2"
        self.call(slice_guard.pre_tool_use, create, slice_guard.load_state("goal-post-session"))
        success_post = {**create, "hook_event_name": "PostToolUse", "tool_response": {"status": "active"}}
        self.call(slice_guard.post_tool_use, success_post, slice_guard.load_state("goal-post-session"))
        self.assertTrue(slice_guard.load_state("goal-post-session")["goal_requested"])

        (self.project / "src" / "tracked.txt").write_text("candidate\n", encoding="utf-8")
        self.call(slice_guard.run_check, type("Args", (), {"session": "goal-post-session", "id": "A1"})())
        self.call(slice_guard.candidate, type("Args", (), {"session": "goal-post-session"})())
        complete = {
            "hook_event_name": "PreToolUse",
            "tool_name": "update_goal",
            "tool_use_id": "goal-complete-1",
            "tool_input": {"status": "complete"},
        }
        _, allowed, _ = self.call(slice_guard.pre_tool_use, complete, slice_guard.load_state("goal-post-session"))
        self.assertEqual(allowed, "")
        self.assertIsNone(slice_guard.load_state("goal-post-session")["goal_status"])
        self.call(
            slice_guard.post_tool_use,
            {**complete, "hook_event_name": "PostToolUse", "tool_response": {"status": "complete"}},
            slice_guard.load_state("goal-post-session"),
        )
        self.assertEqual(slice_guard.load_state("goal-post-session")["goal_status"], "complete")

    def test_vague_goal_and_completion_without_exact_goal_are_rejected(self) -> None:
        self.begin("goal-boundary-session")
        state = slice_guard.load_state("goal-boundary-session")
        vague = {
            "hook_event_name": "PreToolUse",
            "tool_name": "create_goal",
            "tool_input": {"objective": "Get it working"},
        }
        _, output, _ = self.call(slice_guard.pre_tool_use, vague, state)
        self.assertEqual(json.loads(output)["hookSpecificOutput"]["permissionDecision"], "deny")
        (self.project / "src" / "tracked.txt").write_text("candidate\n", encoding="utf-8")
        self.call(slice_guard.run_check, type("Args", (), {"session": "goal-boundary-session", "id": "A1"})())
        self.call(slice_guard.candidate, type("Args", (), {"session": "goal-boundary-session"})())
        state = slice_guard.load_state("goal-boundary-session")
        complete = {
            "hook_event_name": "PreToolUse",
            "tool_name": "update_goal",
            "tool_input": {"status": "complete"},
        }
        _, output, _ = self.call(slice_guard.pre_tool_use, complete, state)
        self.assertEqual(json.loads(output)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_absolute_patch_path_inside_lease_is_allowed(self) -> None:
        self.begin("patch-session")
        state = slice_guard.load_state("patch-session")
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {"command": f"*** Update File: {self.project / 'src' / 'tracked.txt'}"},
        }
        _, output, _ = self.call(slice_guard.pre_tool_use, payload, state)
        self.assertEqual(output, "")

    def test_patch_path_traversal_outside_lease_is_rejected(self) -> None:
        self.begin("traversal-session", self.contract(allowed_paths=["src/allowed"] ))
        state = slice_guard.load_state("traversal-session")
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {"command": "*** Update File: src/allowed/../../docs/drift.txt"},
        }
        _, output, _ = self.call(slice_guard.pre_tool_use, payload, state)
        self.assertEqual(json.loads(output)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_guard_command_cannot_be_chained_to_undeclared_verification(self) -> None:
        self.begin("chain-session")
        state = slice_guard.load_state("chain-session")
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": f'py -3 "{GUARD_PATH}" status --session chain-session; pytest -q'},
        }
        _, output, _ = self.call(slice_guard.pre_tool_use, payload, state)
        self.assertEqual(json.loads(output)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_guard_command_rejects_windows_backslash_separator_fake_path_and_wrong_session(self) -> None:
        self.begin("strict-session")
        state = slice_guard.load_state("strict-session")
        commands = [
            f'py -3 "{GUARD_PATH}" status --session strict-session \\; pytest -q',
            'py -3 "C:\\temp\\slice_guard.py" status --session strict-session',
            f'py -3 "{GUARD_PATH}" status --session another-session',
            "Get-Content (Set-Content docs/outside.txt x)",
            "rg --pre malicious pattern .",
            "git diff --output=docs/outside.patch",
        ]
        for command in commands:
            with self.subTest(command=command):
                payload = {
                    "session_id": "strict-session",
                    "cwd": str(self.project),
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": command},
                }
                _, output, _ = self.call(slice_guard.pre_tool_use, payload, state)
                self.assertEqual(json.loads(output)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_active_slice_denies_unclassified_mutation_for_command_tool_aliases(self) -> None:
        self.begin("commands-session")
        state = slice_guard.load_state("commands-session")
        for tool, command in (
            ("Bash", 'python -c "from pathlib import Path; Path(\'docs/outside.txt\').write_text(\'x\')"'),
            ("shell_command", "git apply patchfile.diff"),
        ):
            with self.subTest(tool=tool):
                payload = {
                    "session_id": "commands-session",
                    "cwd": str(self.project),
                    "hook_event_name": "PreToolUse",
                    "tool_name": tool,
                    "tool_input": {"command": command},
                }
                _, output, _ = self.call(slice_guard.pre_tool_use, payload, state)
                self.assertEqual(json.loads(output)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_active_slice_denies_structured_writers_and_allows_explicit_readers(self) -> None:
        self.begin("structured-session")
        state = slice_guard.load_state("structured-session")
        for tool, tool_input in (
            ("mcp__filesystem__write_file", {"path": "docs/outside.txt", "content": "x"}),
            ("computer_use", {"action": "click", "x": 10, "y": 10}),
        ):
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": tool,
                "tool_input": tool_input,
            }
            _, output, _ = self.call(slice_guard.pre_tool_use, payload, state)
            self.assertEqual(json.loads(output)["hookSpecificOutput"]["permissionDecision"], "deny")
        view = {
            "hook_event_name": "PreToolUse",
            "tool_name": "view_image",
            "tool_input": {"path": str(self.root / "artifact.png")},
        }
        _, output, _ = self.call(slice_guard.pre_tool_use, view, state)
        self.assertEqual(output, "")

    def test_parallel_and_retasking_are_rejected(self) -> None:
        with self.assertRaisesRegex(slice_guard.GuardError, "separate owner-approved workflow"):
            slice_guard.validate_contract(self.contract(subagents="parallel"), self.project)
        self.begin("review-session", self.contract(subagents="reviewer"))
        state = slice_guard.load_state("review-session")
        followup = {
            "hook_event_name": "PreToolUse",
            "tool_name": "followup_task",
            "tool_input": {"message": "Review it again"},
        }
        _, output, _ = self.call(slice_guard.pre_tool_use, followup, state)
        self.assertEqual(json.loads(output)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_reviewer_is_read_only_and_followup_messaging_is_rejected(self) -> None:
        self.begin("review-readonly-session", self.contract(subagents="reviewer"))
        state = slice_guard.load_state("review-readonly-session")
        spawn = {
            "hook_event_name": "PreToolUse",
            "tool_name": "spawn_agent",
            "tool_input": {"message": "Perform one bounded read-only counterexample review"},
        }
        _, output, _ = self.call(slice_guard.pre_tool_use, spawn, state)
        self.assertEqual(output, "")
        start = {"hook_event_name": "SubagentStart"}
        self.call(slice_guard.subagent_start, start, slice_guard.load_state("review-readonly-session"))
        active = slice_guard.load_state("review-readonly-session")
        patch = {
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {"command": "*** Update File: src/tracked.txt"},
        }
        _, denied, _ = self.call(slice_guard.pre_tool_use, patch, active)
        self.assertEqual(json.loads(denied)["hookSpecificOutput"]["permissionDecision"], "deny")
        view = {
            "hook_event_name": "PreToolUse",
            "tool_name": "view_image",
            "tool_input": {"path": str(self.root / "artifact.png")},
        }
        _, allowed, _ = self.call(slice_guard.pre_tool_use, view, active)
        self.assertEqual(allowed, "")
        message = {
            "hook_event_name": "PreToolUse",
            "tool_name": "send_message",
            "tool_input": {"message": "Review another thing"},
        }
        _, denied, _ = self.call(slice_guard.pre_tool_use, message, active)
        self.assertEqual(json.loads(denied)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.call(slice_guard.subagent_stop, {"hook_event_name": "SubagentStop"}, active)
        self.assertFalse(slice_guard.load_state("review-readonly-session")["reviewer_active"])

    def test_v1_state_fails_closed_with_abort_recovery(self) -> None:
        self.begin("migration-session")
        path = slice_guard.state_path("migration-session")
        value = json.loads(path.read_text(encoding="utf-8"))
        value["schema_version"] = 1
        path.write_text(json.dumps(value), encoding="utf-8")
        migrated = slice_guard.load_state("migration-session")
        self.assertEqual(migrated["status"], "migration_required")
        abort_args = type("Args", (), {"session": "migration-session", "reason": "Discard incompatible prior guard state"})()
        self.call(slice_guard.abort, abort_args)
        self.assertEqual(slice_guard.load_state("migration-session")["status"], "aborted")

    def test_candidate_requires_recorded_check_and_blocks_out_of_scope_change(self) -> None:
        self.begin("scope-session")
        candidate_args = type("Args", (), {"session": "scope-session"})()
        with self.assertRaisesRegex(slice_guard.GuardError, "not passed"):
            slice_guard.candidate(candidate_args)
        (self.project / "docs" / "drift.txt").write_text("outside\n", encoding="utf-8")
        run_args = type("Args", (), {"session": "scope-session", "id": "A1"})()
        result, _, _ = self.call(slice_guard.run_check, run_args)
        self.assertEqual(result, 0)
        with self.assertRaisesRegex(slice_guard.GuardError, "outside the slice lease"):
            slice_guard.candidate(candidate_args)

    def test_candidate_blocks_recent_ignored_drift_and_zero_change(self) -> None:
        (self.project / ".gitignore").write_text("*.tmp\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.project), "add", ".gitignore"], check=True)
        subprocess.run(["git", "-C", str(self.project), "commit", "-qm", "ignore temp"], check=True)
        self.begin("ignored-session")
        run_args = type("Args", (), {"session": "ignored-session", "id": "A1"})()
        self.call(slice_guard.run_check, run_args)
        candidate_args = type("Args", (), {"session": "ignored-session"})()
        with self.assertRaisesRegex(slice_guard.GuardError, "No allowed project path changed"):
            slice_guard.candidate(candidate_args)
        (self.project / "src" / "tracked.txt").write_text("allowed\n", encoding="utf-8")
        (self.project / "docs" / "drift.tmp").write_text("ignored drift\n", encoding="utf-8")
        self.call(slice_guard.run_check, run_args)
        with self.assertRaisesRegex(slice_guard.GuardError, "docs/drift.tmp"):
            slice_guard.candidate(candidate_args)

    def test_candidate_rejects_checks_that_predate_current_code(self) -> None:
        self.begin("stale-session")
        self.call(slice_guard.run_check, type("Args", (), {"session": "stale-session", "id": "A1"})())
        (self.project / "src" / "tracked.txt").write_text("changed after check\n", encoding="utf-8")
        with self.assertRaisesRegex(slice_guard.GuardError, "evidence predates"):
            slice_guard.candidate(type("Args", (), {"session": "stale-session"})())

    def test_begin_rejects_preexisting_dirty_allowed_path(self) -> None:
        (self.project / "src" / "tracked.txt").write_text("owner work\n", encoding="utf-8")
        with self.assertRaisesRegex(slice_guard.GuardError, "uncommitted work"):
            self.begin("dirty-session")

    def test_candidate_detects_deleted_baseline_ignored_file(self) -> None:
        (self.project / ".gitignore").write_text("*.tmp\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.project), "add", ".gitignore"], check=True)
        subprocess.run(["git", "-C", str(self.project), "commit", "-qm", "ignore temp"], check=True)
        ignored = self.project / "docs" / "owner.tmp"
        ignored.write_text("owner state\n", encoding="utf-8")
        self.begin("ignored-delete-session")
        ignored.unlink()
        (self.project / "src" / "tracked.txt").write_text("candidate\n", encoding="utf-8")
        self.call(slice_guard.run_check, type("Args", (), {"session": "ignored-delete-session", "id": "A1"})())
        with self.assertRaisesRegex(slice_guard.GuardError, "docs/owner.tmp"):
            slice_guard.candidate(type("Args", (), {"session": "ignored-delete-session"})())

    def test_candidate_status_and_stop_claim_are_bounded(self) -> None:
        self.begin("candidate-session")
        (self.project / "src" / "tracked.txt").write_text("candidate\n", encoding="utf-8")
        run_args = type("Args", (), {"session": "candidate-session", "id": "A1"})()
        self.call(slice_guard.run_check, run_args)
        candidate_args = type("Args", (), {"session": "candidate-session"})()
        result, output, _ = self.call(slice_guard.candidate, candidate_args)
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output)["status"], "candidate_ready")
        state = slice_guard.load_state("candidate-session")
        broad_payload = {
            "hook_event_name": "Stop",
            "last_assistant_message": "The project is complete.\n\nStatus: Candidate ready",
            "stop_hook_active": False,
        }
        _, blocked, _ = self.call(slice_guard.stop_hook, broad_payload, state)
        self.assertEqual(json.loads(blocked)["decision"], "block")
        bounded_payload = dict(broad_payload, last_assistant_message="Status: Candidate ready\n\nThe focused check passed; release was not evaluated.")
        _, allowed, _ = self.call(slice_guard.stop_hook, bounded_payload, state)
        self.assertEqual(json.loads(allowed), {})

    def test_stop_claim_blocks_all_requirements_and_release_phrasing(self) -> None:
        self.begin("claims-session")
        (self.project / "src" / "tracked.txt").write_text("candidate\n", encoding="utf-8")
        self.call(slice_guard.run_check, type("Args", (), {"session": "claims-session", "id": "A1"})())
        self.call(slice_guard.candidate, type("Args", (), {"session": "claims-session"})())
        state = slice_guard.load_state("claims-session")
        for claim in (
            "All requirements passed.",
            "We are ready to release.",
            "The app is done.",
            "All of it is fixed.",
            "EtherPlot is complete.",
            "EtherPlot has reached completion.",
            "The requested work is now finished.",
            "Nothing remains to be done.",
        ):
            payload = {
                "hook_event_name": "Stop",
                "last_assistant_message": f"Status: Candidate ready\n\n{claim}",
                "stop_hook_active": False,
            }
            _, output, _ = self.call(slice_guard.stop_hook, payload, state)
            self.assertEqual(json.loads(output)["decision"], "block")

    def test_observation_remains_pending_independent_acceptance(self) -> None:
        contract = self.contract(acceptance=[
            {
                "id": "A1",
                "kind": "command",
                "criterion": "The focused check passes",
                "command": "Write-Output focused-pass",
            },
            {
                "id": "A2",
                "kind": "observe",
                "criterion": "The visible marker is legible",
            },
        ])
        self.begin("observe-session", contract)
        (self.project / "src" / "tracked.txt").write_text("observed candidate\n", encoding="utf-8")
        artifact = self.root / "current.png"
        artifact.write_bytes(b"current")
        self.call(slice_guard.run_check, type("Args", (), {"session": "observe-session", "id": "A1"})())
        observe_args = type("Args", (), {
            "session": "observe-session",
            "id": "A2",
            "note": "The marker is visible",
            "artifact": [str(artifact)],
        })()
        self.call(slice_guard.observe, observe_args)
        _, output, _ = self.call(slice_guard.candidate, type("Args", (), {"session": "observe-session"})())
        receipt = json.loads(output)
        self.assertEqual(receipt["status"], "candidate_needs_owner")
        self.assertIn("agent-observed A2", receipt["owner_gates"][0])

    def test_candidate_rejects_observation_artifact_changed_after_inspection(self) -> None:
        contract = self.contract(acceptance=[
            {"id": "A1", "kind": "command", "criterion": "The focused check passes", "command": "Write-Output focused-pass"},
            {"id": "A2", "kind": "observe", "criterion": "The visible marker is legible"},
        ])
        self.begin("artifact-stale-session", contract)
        (self.project / "src" / "tracked.txt").write_text("candidate\n", encoding="utf-8")
        artifact = self.root / "current.png"
        artifact.write_bytes(b"first")
        self.call(slice_guard.run_check, type("Args", (), {"session": "artifact-stale-session", "id": "A1"})())
        observe_args = type("Args", (), {
            "session": "artifact-stale-session",
            "id": "A2",
            "note": "The marker is visible",
            "artifact": [str(artifact)],
        })()
        self.call(slice_guard.observe, observe_args)
        artifact.write_bytes(b"changed")
        with self.assertRaisesRegex(slice_guard.GuardError, "Observed artifacts changed"):
            slice_guard.candidate(type("Args", (), {"session": "artifact-stale-session"})())

    def test_installer_preserves_other_hooks_and_is_idempotent(self) -> None:
        installed_guard = self.codex_home / "skills" / "drive-project-work" / "scripts" / "slice_guard.py"
        installed_guard.parent.mkdir(parents=True)
        shutil.copy2(GUARD_PATH, installed_guard)
        installed_hook = self.codex_home / "hooks" / "drive_project_work_hook.py"
        installed_hook.parent.mkdir(parents=True)
        shutil.copy2(HOOK_ADAPTER_PATH, installed_hook)
        hooks_path = self.codex_home / "hooks.json"
        hooks_path.parent.mkdir(parents=True, exist_ok=True)
        hooks_path.write_text(json.dumps({
            "hooks": {
                "Stop": [{"hooks": [{"type": "command", "command": "python other.py"}]}]
            }
        }), encoding="utf-8")
        command = [
            os.environ.get("PYTHON", "python"),
            str(INSTALL_HOOKS_PATH),
            "--codex-home", str(self.codex_home),
            "--hook-script", str(installed_hook),
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, text=True)
        subprocess.run(command, check=True, stdout=subprocess.PIPE, text=True)
        value = json.loads(hooks_path.read_text(encoding="utf-8"))
        stop_groups = value["hooks"]["Stop"]
        other = [group for group in stop_groups if group["hooks"][0].get("command") == "python other.py"]
        managed = [group for group in stop_groups if "drive_project_work_hook.py" in group["hooks"][0].get("command", "")]
        self.assertEqual(len(other), 1)
        self.assertEqual(len(managed), 1)
        windows_command = managed[0]["hooks"][0]["commandWindows"]
        event = json.dumps({
            "session_id": "install-smoke",
            "cwd": str(self.project),
            "hook_event_name": "SessionStart",
            "source": "startup",
        })
        executed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", windows_command],
            input=event,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "CODEX_HOME": str(self.codex_home)},
        )
        self.assertEqual(executed.returncode, 0, executed.stderr)
        self.assertEqual(json.loads(executed.stdout)["hookSpecificOutput"]["hookEventName"], "SessionStart")


if __name__ == "__main__":
    unittest.main()
