#!/usr/bin/env python3
"""Transcript-backed continuity hooks for Codex compaction."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


RECENT_MESSAGE_COUNT = 12
RECENT_TOOL_COUNT = 16
REHYDRATE_USER_COUNT = 8
REHYDRATE_MESSAGE_COUNT = 6
REHYDRATE_CHAR_LIMIT = 28_000
TOOL_EXCERPT_LIMIT = 2_500
SUMMARY_EXCERPT_LIMIT = 8_000

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


def _native_summaries(records: Iterable[dict[str, Any]]) -> list[str]:
    summaries: list[str] = []
    for record in records:
        if record.get("type") != "turn_context":
            continue
        payload = record.get("payload")
        if not isinstance(payload, dict) or not payload.get("summary"):
            continue
        summary = _json_text(payload["summary"])
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
    summaries = _native_summaries(records)
    tools = _tool_activity(records)
    goals = _goal_activity(records)
    context_ratio = _latest_context_ratio(records)
    git_state = _git_snapshot(str(hook_input.get("cwd", "")))
    transcript_hash = hashlib.sha256(transcript_path.read_bytes()).hexdigest()

    recovery_messages = messages[-RECENT_MESSAGE_COUNT:]
    recovery_tools = tools[-RECENT_TOOL_COUNT:]
    injected_users = user_messages[-REHYDRATE_USER_COUNT:]
    injected_messages = messages[-REHYDRATE_MESSAGE_COUNT:]
    summary_text = "\n\n".join(
        _fence(summary[:SUMMARY_EXCERPT_LIMIT]) for summary in summaries
    ) or "(no earlier native compaction summary was present)"
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

## Earlier native compaction summaries

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

    latest_summary = summaries[-1][:SUMMARY_EXCERPT_LIMIT] if summaries else "(none)"
    rehydrate = f"""# Mandatory post-compaction recovery context

The full transcript-derived recovery packet is stored at `{{RECOVERY_PATH}}`. Read it before making a new plan, changing scope, declaring completion, or abandoning an active goal. It preserves every genuine user prompt verbatim. Continue the same task from the latest verified state and do not restart finished work.

Session: `{hook_input.get('session_id', 'unknown')}`  
Working directory: `{hook_input.get('cwd', '')}`  
Snapshot time: `{generated_at.isoformat()}`

## Most recent native summary before this compaction

{_fence(latest_summary)}

## Latest user prompts, verbatim

{_render_messages(injected_users)}

## Latest conversational messages, verbatim

{_render_messages(injected_messages)}

## Git state at the compaction boundary

{_fence(git_state)}
"""

    if len(rehydrate) > REHYDRATE_CHAR_LIMIT:
        half = REHYDRATE_CHAR_LIMIT // 2
        rehydrate = (
            rehydrate[:half]
            + "\n\n... [middle omitted; read the full recovery file] ...\n\n"
            + rehydrate[-half:]
        )

    manifest = {
        "schema_version": 2,
        "generated_at": generated_at.isoformat(),
        "session_id": str(hook_input.get("session_id", "unknown")),
        "turn_id": str(hook_input.get("turn_id", "unknown")),
        "trigger": str(hook_input.get("trigger", hook_input.get("hook_event_name", "unknown"))),
        "cwd": str(hook_input.get("cwd", "")),
        "model": str(hook_input.get("model", "unknown")),
        "transcript_path": str(transcript_path),
        "transcript_sha256": transcript_hash,
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
        },
    }
    return recovery, rehydrate, manifest


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def _snapshot(hook_input: dict[str, Any], snapshot_kind: str) -> Path:
    transcript_value = hook_input.get("transcript_path")
    if not isinstance(transcript_value, str) or not transcript_value:
        raise RecoveryError("Codex did not provide a transcript path")
    transcript_path = Path(transcript_value).expanduser().resolve()
    if not transcript_path.is_file():
        raise RecoveryError(f"transcript does not exist: {transcript_path}")

    generated_at = _utc_now()
    records = _read_records(transcript_path)
    if not records:
        raise RecoveryError("transcript contained no readable JSONL records")

    session_id = _safe_component(str(hook_input.get("session_id", "unknown")))
    session_dir = _continuity_root() / session_id
    recovery_path = session_dir / "recovery.md"
    rehydrate_path = session_dir / "rehydrate.md"
    manifest_path = session_dir / "manifest.json"

    recovery, rehydrate, manifest = _render_recovery(
        hook_input, transcript_path, records, generated_at
    )
    rehydrate = rehydrate.replace("{RECOVERY_PATH}", str(recovery_path))
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

    return f"""# Mandatory visible compaction report

Before any tool call or resumed implementation, send one concise commentary message using exactly this structure:

### Context recovery

- Compaction: {trigger_label} at {ratio_text} observed context usage.
- Context change: <state that Codex does not expose an exact native token-removal map; summarize only evidence-backed categories no longer verbatim in the active handoff; state that all {user_total} user prompts remain verbatim in the full recovery packet and that {injected_users} latest user prompts plus {injected_messages} of {message_total} conversational messages were injected verbatim here>
- Why: {reason}
- Current task: <specific objective recovered from the newest owner instructions and native summary>
- Resuming now: <exact immediate action before performing it>
- Recovery: Successful. The packet, manifest, session identity, and injected handoff were verified; the full packet remains recoverable.

Do not claim an exact removed-token count or invent deleted items. Continue the recovered task in the same turn after posting the report."""


def _load_session(session_id: str) -> tuple[str, dict[str, Any]]:
    session_dir = _continuity_root() / _safe_component(session_id)
    recovery_path = session_dir / "recovery.md"
    rehydrate_path = session_dir / "rehydrate.md"
    manifest_path = session_dir / "manifest.json"
    for path in (recovery_path, rehydrate_path, manifest_path):
        if not path.is_file():
            raise RecoveryError(f"missing {path.name}")
    try:
        recovery_bytes = recovery_path.read_bytes()
        rehydrate_bytes = rehydrate_path.read_bytes()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RecoveryError(f"could not read recovery files: {exc}") from exc
    if not isinstance(manifest, dict):
        raise RecoveryError("manifest is not a JSON object")
    if str(manifest.get("session_id", "")) != session_id:
        raise RecoveryError("manifest session does not match the resumed session")
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
        context, manifest = _load_session(session_id)
    except RecoveryError as exc:
        return {
            "continue": True,
            "systemMessage": f"Continuity recovery {source or 'resume'} failed: {exc}",
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
