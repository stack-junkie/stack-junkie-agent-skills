#!/usr/bin/env python3
"""Transcript-backed continuity hooks for Codex compaction."""

from __future__ import annotations

import datetime as dt
import contextlib
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Iterable


RECENT_MESSAGE_COUNT = 12
RECENT_TOOL_COUNT = 16
REHYDRATE_USER_COUNT = 8
REHYDRATE_MESSAGE_COUNT = 6
REHYDRATE_CHAR_LIMIT = 28_000
TOOL_EXCERPT_LIMIT = 2_500
SUMMARY_EXCERPT_LIMIT = 8_000
GIT_HANDOFF_LIMIT = 6_000
SUMMARY_MODE_MARKERS = {"auto", "manual", "none", "disabled"}

HOST_WRAPPER = re.compile(
    r"\A\s*<(recommended_plugins|environment_context)>.*?</\1>\s*",
    flags=re.DOTALL,
)


class RecoveryError(RuntimeError):
    """Raised when a required recovery snapshot cannot be created or loaded."""


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _safe_component(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return cleaned or "unknown-session"


def _json_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _message_text(payload: dict[str, Any]) -> str:
    pieces: list[str] = []
    content = payload.get("content")
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                pieces.append(part["text"])
    elif isinstance(content, str):
        pieces.append(content)
    return "\n".join(pieces)


def _genuine_user_text(text: str) -> str:
    remaining = text
    while True:
        updated = HOST_WRAPPER.sub("", remaining, count=1)
        if updated == remaining:
            break
        remaining = updated
    return remaining.lstrip("\r\n")


def _read_records(transcript_path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with transcript_path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                parsed["_line_number"] = line_number
                records.append(parsed)
    return records


def _messages(records: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for record in records:
        if record.get("type") != "response_item":
            continue
        payload = record.get("payload")
        if not isinstance(payload, dict) or payload.get("type") != "message":
            continue
        role = payload.get("role")
        if role not in {"user", "assistant"}:
            continue
        text = _message_text(payload)
        if role == "user":
            text = _genuine_user_text(text)
        if text:
            result.append({"role": role, "text": text})
    return result


def _verify_identity(records: list[dict[str, Any]], session_id: str) -> dict[str, Any]:
    metadata = [r.get("payload") for r in records if r.get("type") == "session_meta"]
    if not metadata or not isinstance(metadata[0], dict):
        raise RecoveryError("transcript has no session_meta identity; refusing unverified recovery")
    identity = metadata[0]
    if not session_id or session_id == "unknown" or identity.get("id") != session_id:
        raise RecoveryError("hook session and transcript session_meta.id differ; refusing cross-agent recovery")
    # Forked transcripts retain ancestor session_meta records after their own header.
    allowed = {session_id}
    for item in metadata:
        if not isinstance(item, dict) or item.get("id") not in allowed:
            raise RecoveryError("transcript contains conflicting session identities")
        parent = _parent_identity(item)
        if parent:
            allowed.add(parent)
    return identity


def _parent_identity(metadata: dict[str, Any]) -> str | None:
    parent_id = metadata.get("parent_thread_id")
    source = metadata.get("source")
    if not parent_id and isinstance(source, dict):
        subagent = source.get("subagent")
        spawn = subagent.get("thread_spawn") if isinstance(subagent, dict) else None
        if isinstance(spawn, dict):
            parent_id = spawn.get("parent_thread_id")
    return parent_id if isinstance(parent_id, str) and parent_id else None


def _hook_thread_input(hook_input: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    """Some hosts share session_id across workers; storage belongs to the transcript thread."""
    metadata = next((r.get("payload") for r in records if r.get("type") == "session_meta"), None)
    if not isinstance(metadata, dict) or not isinstance(metadata.get("id"), str):
        raise RecoveryError("transcript has no session_meta identity")
    thread_id = metadata["id"]
    hook_session_id = str(hook_input.get("session_id", ""))
    parent_id = _parent_identity(metadata)
    if not hook_session_id or hook_session_id not in {thread_id, parent_id}:
        raise RecoveryError("hook session and transcript identity are unrelated; refusing cross-agent recovery")
    _verify_identity(records, thread_id)
    return dict(hook_input, session_id=thread_id, hook_session_id=hook_session_id)


def _native_summaries(records: Iterable[dict[str, Any]]) -> list[str]:
    summaries: list[str] = []
    for record in records:
        if record.get("type") != "turn_context":
            continue
        payload = record.get("payload")
        if not isinstance(payload, dict) or not payload.get("summary"):
            continue
        raw_summary = payload["summary"]
        if (
            isinstance(raw_summary, str)
            and raw_summary.strip().lower() in SUMMARY_MODE_MARKERS
        ):
            continue
        summary = _json_text(raw_summary)
        if summary not in summaries:
            summaries.append(summary)
    return summaries


def _tool_activity(records: Iterable[dict[str, Any]]) -> list[str]:
    activity: list[str] = []
    for record in records:
        if record.get("type") != "response_item":
            continue
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue
        if payload.get("type") not in {"custom_tool_call", "custom_tool_call_output"}:
            continue
        rendered = _json_text(payload)
        if len(rendered) > TOOL_EXCERPT_LIMIT:
            rendered = rendered[:TOOL_EXCERPT_LIMIT] + "\n... [excerpt truncated]"
        activity.append(rendered)
    return activity


def _goal_activity(records: Iterable[dict[str, Any]]) -> list[str]:
    result: list[str] = []
    include_next_output = False
    for record in records:
        if record.get("type") != "response_item":
            continue
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue
        payload_type = payload.get("type")
        name = str(payload.get("name", ""))
        if payload_type == "custom_tool_call" and name in {
            "create_goal",
            "get_goal",
            "update_goal",
        }:
            result.append(_json_text(payload))
            include_next_output = True
        elif include_next_output and payload_type == "custom_tool_call_output":
            result.append(_json_text(payload)[:TOOL_EXCERPT_LIMIT])
            include_next_output = False
    return result[-8:]


def _latest_context_ratio(records: Iterable[dict[str, Any]]) -> float | None:
    ratio: float | None = None
    for record in records:
        if record.get("type") != "event_msg":
            continue
        payload = record.get("payload")
        if not isinstance(payload, dict) or payload.get("type") != "token_count":
            continue
        info = payload.get("info")
        if not isinstance(info, dict):
            continue
        usage = info.get("last_token_usage")
        window = info.get("model_context_window")
        if not isinstance(usage, dict) or not isinstance(window, (int, float)) or window <= 0:
            continue
        input_tokens = usage.get("input_tokens")
        if isinstance(input_tokens, (int, float)):
            ratio = min(max(float(input_tokens) / float(window), 0.0), 10.0)
    return ratio


def _git_snapshot(cwd: str) -> str:
    if not cwd:
        return "Unavailable: hook input did not include a working directory."
    try:
        completed = subprocess.run(
            ["git", "-C", cwd, "status", "--short", "--branch"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return f"Unavailable: {exc}"
    output = (completed.stdout or completed.stderr).strip()
    if completed.returncode != 0:
        return "Not a readable Git worktree."
    return output or "Clean worktree (Git returned no status lines)."


def _fence(text: str, language: str = "text") -> str:
    delimiter = "````" if "```" in text else "```"
    return f"{delimiter}{language}\n{text}\n{delimiter}"


def _render_messages(messages: Iterable[dict[str, str]]) -> str:
    sections: list[str] = []
    for index, message in enumerate(messages, start=1):
        sections.append(
            f"### {index}. {message['role'].title()}\n\n{_fence(message['text'])}"
        )
    return "\n\n".join(sections) if sections else "(none found)"


def _bounded_excerpt(text: str, limit: int, label: str) -> str:
    if len(text) <= limit:
        return text
    half = max((limit - len(label) - 10) // 2, 0)
    return text[:half] + f"\n\n... [{label}] ...\n\n" + text[-half:]


def _codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".codex").resolve()


def _continuity_root() -> Path:
    override = os.environ.get("CODEX_CONTINUITY_HOME")
    if override:
        return Path(override).expanduser().resolve()
    return (_codex_home() / "continuity").resolve()


def _render_recovery(
    hook_input: dict[str, Any],
    transcript_path: Path,
    records: list[dict[str, Any]],
    generated_at: dt.datetime,
) -> tuple[str, str, dict[str, Any]]:
    messages = _messages(records)
    user_messages = [message for message in messages if message["role"] == "user"]
    explicit_plans = [m["text"] for m in user_messages if m["text"].lstrip().startswith("PLEASE IMPLEMENT THIS PLAN:")]
    approved_plan = explicit_plans[-1] if explicit_plans else "No explicit Plan Mode approval marker found. Recover the controlling objective from the full user-prompt section; do not infer it from recent messages alone."
    if len(approved_plan) > 12_000:
        approved_plan = "The latest explicit Plan Mode approval is larger than the handoff allowance. Read it verbatim in the full packet before implementation; it has not been partially injected."
    summaries = _native_summaries(records)
    tools = _tool_activity(records)
    goals = _goal_activity(records)
    context_ratio = _latest_context_ratio(records)
    git_state = _git_snapshot(str(hook_input.get("cwd", "")))
    # _snapshot supplies one immutable byte prefix for parsing and hashing.
    transcript_hash = (str(hook_input["_transcript_sha256"]) if "_transcript_sha256" in hook_input
                       else hashlib.sha256(transcript_path.read_bytes()).hexdigest())

    recovery_messages = messages[-RECENT_MESSAGE_COUNT:]
    recovery_tools = tools[-RECENT_TOOL_COUNT:]
    injected_users = user_messages[-REHYDRATE_USER_COUNT:]
    injected_messages = messages[-REHYDRATE_MESSAGE_COUNT:]
    summary_text = "\n\n".join(
        _fence(summary[:SUMMARY_EXCERPT_LIMIT]) for summary in summaries
    ) or "(no substantive earlier summary content was exposed in the transcript)"
    goal_text = "\n\n".join(_fence(item, "json") for item in goals) or "(none found)"
    tool_text = "\n\n".join(_fence(item, "json") for item in recovery_tools) or "(none found)"
    ratio_text = f"{context_ratio:.1%}" if context_ratio is not None else "unknown"

    recovery = f"""# Codex compaction recovery packet

Generated: {generated_at.isoformat()}  
Session: `{hook_input.get('session_id', 'unknown')}`  
Turn: `{hook_input.get('turn_id', 'unknown')}`  
Trigger: `{hook_input.get('trigger', hook_input.get('hook_event_name', 'unknown'))}`  
Model: `{hook_input.get('model', 'unknown')}`  
Working directory: `{hook_input.get('cwd', '')}`  
Latest observed context ratio: `{ratio_text}`  
Transcript: `{transcript_path}`  
Transcript SHA-256: `{transcript_hash}`

## Recovery contract

This packet was created from the local append-only Codex transcript before compaction. User prompts and conversational messages below are verbatim transcript text. Tool records are bounded excerpts. Reconcile this evidence with Codex's native compacted summary. Never discard an active owner request merely because it is absent from that summary. The newest user instruction wins when instructions conflict.

## Earlier summary content exposed in the transcript

{summary_text}

## Every genuine user prompt, verbatim

{_render_messages(user_messages)}

## Recent conversation, verbatim

{_render_messages(recovery_messages)}

## Goal-related records

{goal_text}

## Recent tool activity excerpts

{tool_text}

## Read-only Git state at snapshot time

{_fence(git_state)}
"""

    latest_summary = (
        summaries[-1][:SUMMARY_EXCERPT_LIMIT]
        if summaries
        else "(no substantive earlier summary content was exposed in the transcript)"
    )
    handoff_git_state = _bounded_excerpt(
        git_state, GIT_HANDOFF_LIMIT, "Git state excerpt shortened; read the full recovery file"
    )

    def render_rehydrate() -> str:
        injected_user_texts = {message["text"] for message in injected_users}
        distinct_conversation = [
            message
            for message in injected_messages
            if not (
                message["role"] == "user" and message["text"] in injected_user_texts
            )
        ]
        overlap_note = (
            "User messages from this recent window that already appear in the user-prompt "
            "section are not duplicated below."
            if len(distinct_conversation) != len(injected_messages)
            else "No messages in this recent window overlap the user-prompt section."
        )
        return f"""# Mandatory post-compaction recovery context

The full transcript-derived recovery packet is stored at `{{RECOVERY_PATH}}`. Before resumed implementation, read the original user-approved objective and acceptance requirements from that packet or their verified canonical project file, then reconcile later user corrections and current artifacts. Recent prompts alone are not the task contract. A blocked next action does not replace the objective. Continue independent authorized work and do not restart finished work. Packet integrity does not establish that you understood the task or completed it.

Session: `{hook_input.get('session_id', 'unknown')}`  
Working directory: `{hook_input.get('cwd', '')}`  
Snapshot time: `{generated_at.isoformat()}`

## Last explicit Plan Mode approval, reconcile later corrections before acting

{_fence(approved_plan)}

## Most recent earlier summary content exposed in the transcript

{_fence(latest_summary)}

## Latest user prompts, verbatim

{_render_messages(injected_users)}

## Latest conversational messages, verbatim

{overlap_note}

{_render_messages(distinct_conversation)}

## Git state at the compaction boundary

{_fence(handoff_git_state)}
"""

    rehydrate = render_rehydrate()
    while len(rehydrate) > REHYDRATE_CHAR_LIMIT and injected_users:
        injected_users = injected_users[1:]
        rehydrate = render_rehydrate()
    while len(rehydrate) > REHYDRATE_CHAR_LIMIT and injected_messages:
        injected_messages = injected_messages[1:]
        rehydrate = render_rehydrate()
    if len(rehydrate) > REHYDRATE_CHAR_LIMIT:
        raise RecoveryError("fixed handoff metadata exceeds the character limit")

    manifest = {
        "schema_version": 3,
        "generated_at": generated_at.isoformat(),
        "session_id": str(hook_input.get("session_id", "unknown")),
        "turn_id": str(hook_input.get("turn_id", "unknown")),
        "trigger": str(hook_input.get("trigger", hook_input.get("hook_event_name", "unknown"))),
        "cwd": str(hook_input.get("cwd", "")),
        "model": str(hook_input.get("model", "unknown")),
        "transcript_path": str(transcript_path),
        "transcript_sha256": transcript_hash,
        "transcript_size_bytes": (hook_input["_transcript_size_bytes"] if "_transcript_size_bytes" in hook_input else transcript_path.stat().st_size),
        "transcript_session_id": hook_input["session_id"],
        "hook_session_id": hook_input.get("hook_session_id", hook_input["session_id"]),
        "user_prompt_count": len(user_messages),
        "conversation_message_count": len(messages),
        "latest_context_ratio": context_ratio,
        "preservation": {
            "full_user_prompt_count": len(user_messages),
            "recovery_conversation_message_count": len(recovery_messages),
            "recovery_tool_excerpt_count": len(recovery_tools),
            "injected_user_prompt_count": len(injected_users),
            "injected_conversation_message_count": len(injected_messages),
            "native_summary_count": len(summaries),
            "explicit_plan_injected": bool(explicit_plans and approved_plan == explicit_plans[-1]),
        },
    }
    return recovery, rehydrate, manifest


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    for attempt in range(20):
        try:
            os.replace(temporary, path)
            break
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.025)


@contextlib.contextmanager
def _snapshot_lock(session_id: str):
    directory = _continuity_root() / _safe_component(session_id)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".snapshot.lock").open("a+b") as lock:
        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        deadline = time.monotonic() + 10
        while True:
            try:
                lock.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise RecoveryError("another snapshot still owns this thread; retry after it completes")
                time.sleep(0.025)
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _snapshot(hook_input: dict[str, Any], snapshot_kind: str) -> Path:
    value = hook_input.get("transcript_path")
    if not isinstance(value, str) or not value:
        raise RecoveryError("Codex did not provide a transcript path")
    with Path(value).expanduser().open(encoding="utf-8") as stream:
        header = json.loads(stream.readline())
    normalized = _hook_thread_input(hook_input, [header])
    with _snapshot_lock(normalized["session_id"]):
        return _snapshot_unlocked(hook_input, snapshot_kind)


def _snapshot_unlocked(hook_input: dict[str, Any], snapshot_kind: str) -> Path:
    transcript_value = hook_input.get("transcript_path")
    if not isinstance(transcript_value, str) or not transcript_value:
        raise RecoveryError("Codex did not provide a transcript path")
    transcript_path = Path(transcript_value).expanduser().resolve()
    if not transcript_path.is_file():
        raise RecoveryError(f"transcript does not exist: {transcript_path}")

    generated_at = _utc_now()
    transcript_bytes = transcript_path.read_bytes()
    records = []
    for line_number, line in enumerate(transcript_bytes.decode("utf-8").splitlines(), 1):
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            parsed["_line_number"] = line_number
            records.append(parsed)
    if not records:
        raise RecoveryError("transcript contained no readable JSONL records")

    hook_input = _hook_thread_input(hook_input, records)
    raw_session_id = str(hook_input.get("session_id", "unknown"))
    identity = _verify_identity(records, raw_session_id)
    hook_input = dict(hook_input, _transcript_sha256=hashlib.sha256(transcript_bytes).hexdigest(),
                      _transcript_size_bytes=len(transcript_bytes))
    session_id = _safe_component(raw_session_id)
    session_dir = _continuity_root() / session_id
    generation = "generations/" + uuid.uuid4().hex
    recovery_path = session_dir / generation / "recovery.md"
    rehydrate_path = session_dir / generation / "rehydrate.md"
    manifest_path = session_dir / "manifest.json"

    recovery, rehydrate, manifest = _render_recovery(
        hook_input, transcript_path, records, generated_at
    )
    rehydrate = rehydrate.replace("{RECOVERY_PATH}", str(recovery_path))
    manifest["generation"] = generation
    manifest["agent_path"] = identity.get("agent_path")
    manifest["parent_thread_id"] = _parent_identity(identity)
    manifest["recovery_sha256"] = hashlib.sha256(recovery.encode("utf-8")).hexdigest()
    manifest["rehydrate_sha256"] = hashlib.sha256(rehydrate.encode("utf-8")).hexdigest()
    _atomic_write(recovery_path, recovery)
    _atomic_write(rehydrate_path, rehydrate)
    _atomic_write(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    timestamp = generated_at.strftime("%Y%m%dT%H%M%S.%fZ")
    archive_path = session_dir / "snapshots" / f"{timestamp}-{_safe_component(snapshot_kind)}.md"
    _atomic_write(archive_path, recovery)
    return recovery_path


def _report_directive(manifest: dict[str, Any]) -> str:
    preservation = manifest.get("preservation")
    if not isinstance(preservation, dict):
        raise RecoveryError("manifest lacks preservation counts")
    trigger = str(manifest.get("trigger", "unknown")).lower()
    if trigger == "auto":
        trigger_label = "Automatic"
        reason = "Automatic compaction reclaimed context-window capacity."
    elif trigger == "manual":
        trigger_label = "Manual"
        reason = "Manual compaction was requested to reduce the active context."
    else:
        trigger_label = "Unknown"
        reason = "The recovery manifest did not identify why compaction was triggered."
    ratio = manifest.get("latest_context_ratio")
    ratio_text = f"{float(ratio):.1%}" if isinstance(ratio, (int, float)) else "unknown"
    user_total = int(manifest.get("user_prompt_count", 0))
    message_total = int(manifest.get("conversation_message_count", 0))
    injected_users = int(preservation.get("injected_user_prompt_count", 0))
    injected_messages = int(preservation.get("injected_conversation_message_count", 0))
    recovery_messages = int(preservation.get("recovery_conversation_message_count", 0))

    return f"""# Mandatory visible compaction report

Before any tool call or resumed implementation, send one concise commentary message using exactly this structure:

### Context recovery

- Compaction: {trigger_label} at {ratio_text} observed context usage.
- Context change: <plainly name the earlier material represented by summaries instead of word-for-word text in the active handoff; state that Codex does not expose an exact before-and-after token diff>
- Preserved evidence: The source transcript contained {message_total} user or assistant messages at snapshot time. The full recovery packet preserves all {user_total} user prompts and the latest {recovery_messages} user or assistant messages word-for-word, plus bounded work evidence.
- Active handoff: It loaded {injected_users} recent user prompts and {injected_messages} recent user or assistant messages word-for-word. These two selections can overlap when a recent message is a user prompt; overlapping text appears once, so do not add the counts together or interpret messages outside these selections as deleted.
- Why: {reason}
- Current task: <specific objective recovered from the newest owner instructions and available recovery evidence>
- Resuming now: <exact immediate action before performing it>
- Recovery: Packet hashes and transcript identity verified. Task understanding and acceptance remain to be reconciled against the original approval and latest corrections.

Do not claim an exact removed-token count or invent deleted items. Do not call a transcript setting such as `summary: "auto"` summary content. Continue the recovered task in the same turn after posting the report."""


def _load_session(session_id: str, hook_input: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
    session_dir = _continuity_root() / _safe_component(session_id)
    manifest_path = session_dir / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RecoveryError(f"could not read manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise RecoveryError("manifest is not a JSON object")
    generation = manifest.get("generation", "")
    if generation and (not isinstance(generation, str) or not re.fullmatch(r"generations/[a-f0-9]{32}", generation)):
        raise RecoveryError("invalid packet generation")
    recovery_path = session_dir / generation / "recovery.md"
    rehydrate_path = session_dir / generation / "rehydrate.md"
    for path in (recovery_path, rehydrate_path, manifest_path):
        if not path.is_file():
            raise RecoveryError(f"missing {path.name}")
    try:
        recovery_bytes = recovery_path.read_bytes()
        rehydrate_bytes = rehydrate_path.read_bytes()
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RecoveryError(f"could not read recovery files: {exc}") from exc
    if not isinstance(manifest, dict):
        raise RecoveryError("manifest is not a JSON object")
    if str(manifest.get("session_id", "")) != session_id:
        raise RecoveryError("manifest session does not match the resumed session")
    transcript_path = Path(str(manifest.get("transcript_path", "")))
    try:
        _verify_identity(_read_records(transcript_path), session_id)
        if hook_input and hook_input.get("transcript_path"):
            current_path = Path(hook_input["transcript_path"]).resolve()
            _verify_identity(_read_records(current_path), session_id)
            if current_path != transcript_path.resolve():
                raise RecoveryError("resumed transcript path differs from snapshot")
        size = manifest.get("transcript_size_bytes")
        if isinstance(size, int) and size >= 0:
            with transcript_path.open("rb") as stream:
                prefix_hash = hashlib.sha256(stream.read(size)).hexdigest()
            if prefix_hash != manifest.get("transcript_sha256"):
                raise RecoveryError("source transcript prefix hash differs from snapshot")
        else:
            raise RecoveryError("legacy packet lacks verifiable transcript prefix; create a fresh identity-checked snapshot")
    except (OSError, UnicodeError) as exc:
        raise RecoveryError(f"could not verify source transcript: {exc}") from exc
    if hashlib.sha256(recovery_bytes).hexdigest() != manifest.get("recovery_sha256"):
        raise RecoveryError("recovery packet hash does not match the manifest")
    if hashlib.sha256(rehydrate_bytes).hexdigest() != manifest.get("rehydrate_sha256"):
        raise RecoveryError("injected handoff hash does not match the manifest")
    try:
        context = rehydrate_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise RecoveryError(f"injected handoff is not UTF-8: {exc}") from exc
    return context, manifest


def _handle_pre_compact(hook_input: dict[str, Any]) -> dict[str, Any]:
    try:
        _snapshot(hook_input, str(hook_input.get("trigger", "compact")))
    except Exception as exc:
        return {
            "continue": False,
            "stopReason": f"Compaction recovery snapshot failed: {exc}",
            "systemMessage": "Compaction stopped because the continuity packet could not be written.",
        }
    return {"continue": True}


def _handle_session_start(hook_input: dict[str, Any]) -> dict[str, Any]:
    session_id = str(hook_input.get("session_id", "unknown"))
    source = str(hook_input.get("source", ""))
    try:
        if hook_input.get("transcript_path"):
            hook_input = _hook_thread_input(hook_input, _read_records(Path(hook_input["transcript_path"])))
            session_id = hook_input["session_id"]
        context, manifest = _load_session(session_id, hook_input)
    except (RecoveryError, OSError, UnicodeError) as exc:
        return {
            "continue": True,
            "systemMessage": f"Continuity recovery {source or 'resume'} failed: {exc}. Do not claim recovery succeeded. Recover the original approval from the matching root transcript or verified project plan before implementation; do not use a worker packet as root authority.",
        }
    if source == "compact":
        context = _report_directive(manifest) + "\n\n" + context
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        },
    }


def handle(hook_input: dict[str, Any]) -> dict[str, Any]:
    event = hook_input.get("hook_event_name")
    if event == "PreCompact":
        return _handle_pre_compact(hook_input)
    if event == "SessionStart" and hook_input.get("source") in {"compact", "resume"}:
        return _handle_session_start(hook_input)
    return {"continue": True}


def main() -> int:
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        hook_input = json.load(sys.stdin)
        if not isinstance(hook_input, dict):
            raise ValueError("hook input must be a JSON object")
        result = handle(hook_input)
    except Exception as exc:
        result = {
            "continue": False,
            "stopReason": f"Continuity hook could not parse its input: {exc}",
            "systemMessage": "Continuity hook failed before it could inspect the event.",
        }
    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
