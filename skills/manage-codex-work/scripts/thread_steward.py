#!/usr/bin/env python3
"""Read-only Codex conversation scanner and small Thread Steward state manager."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from typing import Any, Iterable


SCHEMA_VERSION = 1
DEFAULT_DAYS = 14
PAGE_SIZE = 100
MAX_PAGES = 20
REQUEST_TIMEOUT_SECONDS = 30.0
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
ISSUE_RE = re.compile(r"(?<!\w)#\d+\b")
UUID_IN_TEXT_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f-]{27,36}\b", re.I)
FILE_RE = re.compile(r"\b[\w.-]+\.(?:cpp|h|hpp|py|ps1|md|json|toml|yaml|yml|tsx|ts|jsx|js|cs)\b", re.I)
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.-]{2,}", re.I)
VISUAL_REQUEST_RE = re.compile(
    r"\b(?:ui|layout|screen|visual|appearance|animation)\b|user interface|tab group|playback preview",
    re.I,
)
STOPWORDS = {
    "about", "after", "again", "agent", "also", "been", "before", "being", "can", "chat",
    "codex", "could", "current", "does", "doing", "from", "have", "into", "just", "like",
    "make", "more", "need", "other", "please", "project", "should", "that", "their", "them",
    "then", "there", "these", "they", "this", "those", "through", "want", "what", "when",
    "where", "which", "with", "work", "would", "your",
}
NEEDS_OWNER_PATTERNS = (
    "need your input", "need your decision", "owner decision", "please confirm", "which option",
    "choose one", "waiting for you", "requires your approval", "what do you want",
)
RISK_MACHINERY_PATTERNS = (
    "validation framework", "validator", "evidence matrix", "acceptance registry", "evaluation harness",
    "screenshot collection", "custom probe", "llm judge",
)
DIRECT_OBSERVATION_PATTERNS = (
    "opened the app", "opened the application", "launched the app", "launched the application",
    "computer use", "inspected the interface", "inspected the ui", "clicked through", "playback preview",
)
COMPLETION_CLAIM_PATTERNS = ("implemented", "complete", "completed", "done", "all tests passed")
HANDOFF_PATTERNS = (
    "previous chat", "other chat", "another chat", "take over", "continue", "moved", "where did",
    "left off", "predecessor", "restart from", "finish the existing",
)
GENERIC_IDENTIFIERS = {
    "agents.md", "changelog.md", "package.json", "readme.md", "skill.md", "version",
    "openai.yaml", "config.toml",
}


class ThreadStewardError(RuntimeError):
    """A concise, user-actionable Thread Steward failure."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def epoch_iso(value: Any) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    return iso_time(datetime.fromtimestamp(value, timezone.utc))


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def steward_home() -> Path:
    configured = os.environ.get("CODEX_THREAD_STEWARD_HOME")
    return Path(configured).expanduser() if configured else codex_home() / "thread-steward"


def package_version() -> str:
    version_file = Path(__file__).resolve().parents[1] / "VERSION"
    try:
        return version_file.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise ThreadStewardError(f"Thread Steward VERSION is unreadable: {version_file}: {exc}") from exc


def new_state() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "last_review_id": None,
        "last_review_at": None,
        "workstreams": {},
        "dispatch_receipts": [],
    }


class StateStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or steward_home() / "state.json"

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return new_state()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ThreadStewardError(f"Thread Steward state is unreadable: {self.path}: {exc}") from exc
        if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
            raise ThreadStewardError(
                f"Unsupported Thread Steward state schema in {self.path}; expected {SCHEMA_VERSION}"
            )
        if not isinstance(data.get("workstreams"), dict):
            raise ThreadStewardError(f"Thread Steward state has invalid workstreams: {self.path}")
        data.setdefault("dispatch_receipts", [])
        data.setdefault("last_review_id", None)
        data.setdefault("last_review_at", None)
        return data

    def save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.{os.getpid()}.tmp")
        try:
            temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            os.replace(temporary, self.path)
        finally:
            if temporary.exists():
                temporary.unlink()


def resolve_codex_command() -> list[str]:
    configured = os.environ.get("CODEX_CLI")
    if configured:
        return [configured]
    if os.name == "nt":
        command = shutil.which("codex.cmd") or shutil.which("codex.exe")
    else:
        command = shutil.which("codex")
    if not command:
        raise ThreadStewardError("Codex CLI was not found; set CODEX_CLI to its executable path")
    return [command]


class AppServerClient:
    """Minimal JSONL client exposing only read operations used by this release."""

    def __init__(self, timeout: float = REQUEST_TIMEOUT_SECONDS) -> None:
        self.timeout = timeout
        self.process: subprocess.Popen[str] | None = None
        self.messages: queue.Queue[str] = queue.Queue()
        self.reader: threading.Thread | None = None
        self.next_id = 1

    def __enter__(self) -> "AppServerClient":
        command = resolve_codex_command() + ["app-server", "--stdio"]
        try:
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as exc:
            raise ThreadStewardError(f"Could not start Codex App Server: {exc}") from exc
        assert self.process.stdout is not None
        self.reader = threading.Thread(target=self._read_stdout, daemon=True)
        self.reader.start()
        self._request(
            "initialize",
            {
                "clientInfo": {
                    "name": "thread-steward",
                    "title": "Thread Steward",
                    "version": package_version(),
                },
                "capabilities": {"experimentalApi": True},
            },
        )
        self._send({"method": "initialized"})
        return self

    def __exit__(self, _type: Any, _value: Any, _traceback: Any) -> None:
        if not self.process:
            return
        try:
            if self.process.stdin:
                self.process.stdin.close()
            self.process.terminate()
            self.process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            self.process.kill()

    def _read_stdout(self) -> None:
        assert self.process and self.process.stdout
        for line in self.process.stdout:
            self.messages.put(line)

    def _send(self, message: dict[str, Any]) -> None:
        if not self.process or not self.process.stdin:
            raise ThreadStewardError("Codex App Server is not running")
        self.process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        self._send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            if self.process and self.process.poll() is not None and self.messages.empty():
                raise ThreadStewardError(f"Codex App Server exited while handling {method}")
            try:
                line = self.messages.get(timeout=0.25)
            except queue.Empty:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if message.get("id") != request_id:
                continue
            if message.get("error"):
                raise ThreadStewardError(f"Codex {method} failed: {message['error']}")
            result = message.get("result")
            return result if isinstance(result, dict) else {}
        raise ThreadStewardError(f"Timed out waiting for Codex {method}")

    def list_recent(self, cutoff_epoch: int) -> list[dict[str, Any]]:
        cursor: str | None = None
        threads: list[dict[str, Any]] = []
        for _ in range(MAX_PAGES):
            params: dict[str, Any] = {
                "limit": PAGE_SIZE,
                "sortKey": "recency_at",
                "sortDirection": "desc",
                "useStateDbOnly": False,
            }
            if cursor:
                params["cursor"] = cursor
            response = self._request("thread/list", params)
            page = response.get("data", [])
            if not isinstance(page, list):
                raise ThreadStewardError("Codex thread/list returned invalid data")
            threads.extend(item for item in page if isinstance(item, dict))
            cursor = response.get("nextCursor")
            recencies = [
                item.get("recencyAt") or item.get("updatedAt") or item.get("createdAt")
                for item in page
                if isinstance(item, dict)
            ]
            oldest = min((value for value in recencies if isinstance(value, int)), default=None)
            if not cursor or oldest is None or oldest < cutoff_epoch:
                break
        return threads

    def read_thread(self, thread_id: str, include_turns: bool = True) -> dict[str, Any]:
        response = self._request(
            "thread/read", {"threadId": thread_id, "includeTurns": include_turns}
        )
        thread = response.get("thread", response)
        if not isinstance(thread, dict) or thread.get("id") != thread_id:
            raise ThreadStewardError(f"Codex thread/read returned invalid data for {thread_id}")
        return thread


def loaded_thread_ids(home: Path | None = None) -> set[str]:
    lock_dir = (home or codex_home()) / "thread-writer-locks"
    if not lock_dir.is_dir():
        return set()
    loaded: set[str] = set()
    for path in lock_dir.glob("*.lock"):
        if not UUID_RE.fullmatch(path.stem):
            continue
        try:
            with path.open("r+b"):
                pass
        except (PermissionError, OSError):
            loaded.add(path.stem)
    return loaded


def text_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content") or item.get("message")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return ""


def item_text(item: dict[str, Any]) -> str:
    for key in ("content", "text", "message"):
        text = text_content(item.get(key))
        if text:
            return text.strip()
    return ""


def thread_messages(thread: dict[str, Any]) -> tuple[list[tuple[str, str]], list[str]]:
    messages: list[tuple[str, str]] = []
    commands: list[str] = []
    for turn in thread.get("turns", []):
        if not isinstance(turn, dict):
            continue
        for item in turn.get("items", []):
            if not isinstance(item, dict):
                continue
            kind = item.get("type")
            if kind == "userMessage":
                text = item_text(item)
                if text:
                    messages.append(("user", text))
            elif kind == "agentMessage":
                text = item_text(item)
                if text:
                    messages.append(("assistant", text))
            elif kind in {"commandExecution", "commandExecutionItem"}:
                command = item.get("command")
                if isinstance(command, list):
                    command = " ".join(str(part) for part in command)
                if isinstance(command, str) and command.strip():
                    commands.append(" ".join(command.split()))
    return messages, commands


def compact(value: str, limit: int) -> str:
    value = " ".join(value.split())
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def latest_turn_status(thread: dict[str, Any]) -> str | None:
    turns = thread.get("turns", [])
    if not isinstance(turns, list) or not turns:
        return None
    last = turns[-1]
    return last.get("status") if isinstance(last, dict) else None


def risk_signals(messages: list[tuple[str, str]], commands: list[str]) -> list[str]:
    joined = "\n".join(text.lower() for _, text in messages[-20:])
    user_messages = [text.lower() for role, text in messages if role == "user"]
    agent_messages = [text.lower() for role, text in messages if role == "assistant"]
    current_user = user_messages[-1] if user_messages else ""
    current_agent = agent_messages[-1] if agent_messages else ""
    signals: list[str] = []
    visual = bool(VISUAL_REQUEST_RE.search(current_user))
    machinery = any(
        re.search(
            rf"\b(?:add(?:ed|ing)?|build(?:ing|t)?|creat(?:e|ed|ing)|implement(?:ed|ing)?|writ(?:e|ing))\b"
            rf".{{0,100}}\b{re.escape(pattern)}\b",
            message,
        )
        for message in [current_agent]
        for pattern in RISK_MACHINERY_PATTERNS
    )
    observed = any(pattern in joined for pattern in DIRECT_OBSERVATION_PATTERNS)
    completion_claim = any(pattern in current_agent for pattern in COMPLETION_CLAIM_PATTERNS)
    if visual and machinery and not observed:
        signals.append("validation machinery appears before direct observation of a visible result")
    if visual and completion_claim and not observed:
        signals.append("visible outcome may be claimed complete without direct UI observation")
    duplicates = [command for command, count in Counter(commands).items() if count >= 3]
    if duplicates:
        signals.append("the same command appears at least three times in the recorded turns")
    if "validation theater" in current_user or "validation theatre" in current_user:
        signals.append("the owner explicitly identified validation theater as a concern")
    return signals


def suggested_category(
    thread: dict[str, Any], messages: list[tuple[str, str]], risks: list[str], parked: str | None
) -> tuple[str, list[str]]:
    if parked:
        return parked, ["owner-recorded workstream state"]
    reasons: list[str] = []
    if risks:
        return "at_risk", risks
    status = latest_turn_status(thread)
    last_role, last_text = messages[-1] if messages else (None, "")
    lowered = last_text.lower()
    if status in {"interrupted", "failed", "cancelled"}:
        return "needs_you", [f"latest recorded turn is {status}"]
    if last_role == "assistant" and (
        "?" in last_text or any(pattern in lowered for pattern in NEEDS_OWNER_PATTERNS)
    ):
        return "needs_you", ["latest assistant message appears to request owner input"]
    if status and status not in {"completed", "interrupted", "failed", "cancelled"}:
        return "working", [f"latest recorded turn status is {status}"]
    if last_role == "user":
        return "working", ["latest recorded conversational message is from the owner"]
    return "review", reasons


def thread_text(thread: dict[str, Any]) -> str:
    return " ".join(
        str(thread.get(key) or "")
        for key in ("name", "preview", "owner_context", "latest_user", "latest_agent")
    )


def thread_tokens(thread: dict[str, Any]) -> set[str]:
    source = thread_text(thread).lower()
    return {token for token in TOKEN_RE.findall(source) if token not in STOPWORDS and not token.isdigit()}


def identifiers(thread: dict[str, Any]) -> set[str]:
    source = thread_text(thread)
    found = {match.lower() for match in ISSUE_RE.findall(source)}
    found.update(match.lower() for match in UUID_IN_TEXT_RE.findall(source))
    found.update(match.lower() for match in FILE_RE.findall(source))
    return {value for value in found if value not in GENERIC_IDENTIFIERS}


def relationship_candidates(
    threads: list[dict[str, Any]], state: dict[str, Any]
) -> list[dict[str, Any]]:
    by_id = {thread["id"]: thread for thread in threads}
    candidates: dict[tuple[str, str], dict[str, Any]] = {}

    def add(
        left: str, right: str, confidence: str, evidence: Iterable[str], score: float = 0.0
    ) -> None:
        if left == right or left not in by_id or right not in by_id:
            return
        key = tuple(sorted((left, right)))
        rank = {"possible": 1, "strong": 2, "confirmed": 3}
        candidate = {
            "thread_ids": list(key),
            "confidence": confidence,
            "evidence": sorted(set(evidence)),
            "_score": score,
        }
        previous = candidates.get(key)
        if not previous or rank[confidence] > rank[previous["confidence"]]:
            candidates[key] = candidate
        elif previous:
            previous["evidence"] = sorted(set(previous["evidence"]) | set(candidate["evidence"]))
            previous["_score"] = max(previous["_score"], score)

    for workstream_id, workstream in state.get("workstreams", {}).items():
        if not isinstance(workstream, dict):
            continue
        canonical = workstream.get("canonical_thread_id")
        for related in workstream.get("related_thread_ids", []):
            if isinstance(canonical, str) and isinstance(related, str):
                add(canonical, related, "confirmed", [f"owner-confirmed workstream {workstream_id}"])

    for thread in threads:
        for relation_key in ("parentThreadId", "forkedFromId"):
            related = thread.get(relation_key)
            if isinstance(related, str):
                add(thread["id"], related, "strong", [relation_key])

    token_map = {thread["id"]: thread_tokens(thread) for thread in threads}
    identifier_map = {thread["id"]: identifiers(thread) for thread in threads}
    text_map = {thread["id"]: thread_text(thread).lower() for thread in threads}
    for index, left in enumerate(threads):
        for right in threads[index + 1 :]:
            left_id, right_id = left["id"], right["id"]
            shared_ids = identifier_map[left_id] & identifier_map[right_id]
            same_cwd = bool(left.get("cwd") and left.get("cwd") == right.get("cwd"))
            shared_tokens = token_map[left_id] & token_map[right_id]
            union = token_map[left_id] | token_map[right_id]
            similarity = len(shared_tokens) / len(union) if union else 0.0
            text = " ".join(
                str(value or "")
                for value in (
                    left.get("preview"), left.get("latest_user"), right.get("preview"), right.get("latest_user")
                )
            ).lower()
            handoff = any(pattern in text for pattern in HANDOFF_PATTERNS)
            explicit_reference = right_id.lower() in text_map[left_id] or left_id.lower() in text_map[right_id]
            unique_ids = {value for value in shared_ids if not value.startswith("#")}
            issue_ids = shared_ids - unique_ids
            if explicit_reference:
                add(left_id, right_id, "strong", ["one conversation explicitly names the other thread ID"], 1.0)
            elif unique_ids:
                add(
                    left_id,
                    right_id,
                    "strong",
                    [f"shared distinctive identifiers: {', '.join(sorted(unique_ids)[:5])}"],
                    0.9,
                )
            elif issue_ids and same_cwd and len(shared_tokens) >= 3:
                add(
                    left_id,
                    right_id,
                    "strong" if len(shared_tokens) >= 5 else "possible",
                    [f"shared issue identifiers: {', '.join(sorted(issue_ids)[:5])}", "same working directory"],
                    0.7 + similarity,
                )
            elif same_cwd and similarity >= 0.25 and len(shared_tokens) >= 4:
                add(left_id, right_id, "possible", ["same working directory", "distinctive text overlap"], similarity)
            elif (
                handoff
                and len(shared_tokens) >= 3
                and ((same_cwd and similarity >= 0.15) or similarity >= 0.28)
            ):
                evidence = ["possible objective overlap"]
                if same_cwd:
                    evidence.append("same working directory")
                if handoff:
                    evidence.append("handoff language")
                add(left_id, right_id, "possible", evidence, similarity)

    fixed = [item for item in candidates.values() if item["confidence"] != "possible"]
    possible = sorted(
        (item for item in candidates.values() if item["confidence"] == "possible"),
        key=lambda item: (-item["_score"], item["thread_ids"]),
    )
    possible_counts: Counter[str] = Counter()
    bounded: list[dict[str, Any]] = []
    for item in possible:
        left_id, right_id = item["thread_ids"]
        if possible_counts[left_id] >= 3 or possible_counts[right_id] >= 3:
            continue
        possible_counts[left_id] += 1
        possible_counts[right_id] += 1
        bounded.append(item)
    result = fixed + bounded
    for item in result:
        item.pop("_score", None)
    return sorted(
        result,
        key=lambda item: ({"confirmed": 0, "strong": 1, "possible": 2}[item["confidence"]], item["thread_ids"]),
    )


def tracked_thread_ids(state: dict[str, Any]) -> set[str]:
    tracked: set[str] = set()
    for workstream in state.get("workstreams", {}).values():
        if not isinstance(workstream, dict):
            continue
        canonical = workstream.get("canonical_thread_id")
        if isinstance(canonical, str):
            tracked.add(canonical)
        tracked.update(item for item in workstream.get("related_thread_ids", []) if isinstance(item, str))
    return tracked


def workstream_state_for_thread(
    thread_id: str, state: dict[str, Any], review_id: str, now: datetime
) -> str | None:
    for workstream in state.get("workstreams", {}).values():
        if not isinstance(workstream, dict):
            continue
        thread_ids = {workstream.get("canonical_thread_id"), *workstream.get("related_thread_ids", [])}
        if thread_id not in thread_ids:
            continue
        status = workstream.get("status")
        if status != "parked":
            return None
        park = workstream.get("park", {})
        trigger_type = park.get("trigger_type")
        trigger_value = park.get("trigger_value")
        if trigger_type == "next_review" and park.get("parked_at_review") != review_id:
            return "due_to_resurface"
        if trigger_type == "date":
            due = parse_time(trigger_value)
            if due and due <= now:
                return "due_to_resurface"
        return "parked"
    return None


def prepare_thread(
    thread: dict[str, Any],
    state: dict[str, Any],
    review_id: str,
    now: datetime,
    loaded: set[str],
    current_thread_id: str | None = None,
) -> dict[str, Any]:
    messages, commands = thread_messages(thread)
    users = [text for role, text in messages if role == "user"]
    agents = [text for role, text in messages if role == "assistant"]
    risks = risk_signals(messages, commands)
    parked = workstream_state_for_thread(thread["id"], state, review_id, now)
    is_current = thread["id"] == current_thread_id
    if is_current:
        category, reasons = "current", ["current Thread Steward conversation"]
    else:
        category, reasons = suggested_category(thread, messages, risks, parked)
    return {
        "id": thread["id"],
        "name": thread.get("name"),
        "preview": compact(str(thread.get("preview") or ""), 320),
        "cwd": thread.get("cwd"),
        "created_at": epoch_iso(thread.get("createdAt")),
        "updated_at": epoch_iso(thread.get("updatedAt")),
        "recency_at": epoch_iso(thread.get("recencyAt")),
        "source": thread.get("source"),
        "runtime_status": thread.get("status"),
        "latest_turn_status": latest_turn_status(thread),
        "is_current": is_current,
        "loaded_in_codex": thread["id"] in loaded,
        "parent_thread_id": thread.get("parentThreadId"),
        "forked_from_id": thread.get("forkedFromId"),
        "latest_user": compact(users[-1], 500) if users else None,
        "latest_agent": compact(agents[-1], 500) if agents else None,
        "owner_context": compact("\n".join(users[-4:]), 1000) if users else None,
        "suggested_category": category,
        "category_evidence": reasons,
        "risk_signals": risks,
    }


def scan(args: argparse.Namespace) -> int:
    now = parse_time(args.now) if args.now else utc_now()
    if now is None:
        raise ThreadStewardError(f"Invalid --now timestamp: {args.now}")
    store = StateStore(Path(args.state_file) if args.state_file else None)
    state = store.load()
    review_id = now.strftime("%Y%m%dT%H%M%S.%fZ")
    cutoff = now - timedelta(days=args.days)
    loaded = loaded_thread_ids(Path(args.codex_home) if args.codex_home else None)
    tracked = tracked_thread_ids(state)
    read_errors: list[dict[str, str]] = []
    with AppServerClient(timeout=args.timeout) as client:
        listed = client.list_recent(int(cutoff.timestamp()))
        metadata = {
            item["id"]: item
            for item in listed
            if isinstance(item.get("id"), str)
            and (
                (item.get("recencyAt") or item.get("updatedAt") or item.get("createdAt") or 0)
                >= cutoff.timestamp()
                or item["id"] in loaded
                or item["id"] in tracked
            )
        }
        for thread_id in sorted((loaded | tracked) - set(metadata)):
            try:
                metadata[thread_id] = client.read_thread(thread_id, include_turns=False)
            except ThreadStewardError as exc:
                read_errors.append({"thread_id": thread_id, "error": str(exc)})
        ordered = sorted(
            metadata.values(),
            key=lambda item: item.get("recencyAt") or item.get("updatedAt") or item.get("createdAt") or 0,
            reverse=True,
        )[: args.max_threads]
        prepared: list[dict[str, Any]] = []
        for item in ordered:
            thread_id = item["id"]
            try:
                full = client.read_thread(thread_id, include_turns=True)
                prepared.append(
                    prepare_thread(full, state, review_id, now, loaded, args.current_thread_id)
                )
            except ThreadStewardError as exc:
                read_errors.append({"thread_id": thread_id, "error": str(exc)})

    relationships = relationship_candidates(prepared, state)
    counts = Counter(thread["suggested_category"] for thread in prepared)
    result = {
        "schema_version": SCHEMA_VERSION,
        "mode": "read_only",
        "review_id": review_id,
        "scanned_at": iso_time(now),
        "window_days": args.days,
        "current_thread_id": args.current_thread_id,
        "cutoff": iso_time(cutoff),
        "thread_count": len(prepared),
        "category_counts": dict(sorted(counts.items())),
        "threads": prepared,
        "relationship_candidates": relationships,
        "read_errors": read_errors,
        "action_gate": {
            "dispatch_enabled": False,
            "steering_enabled": False,
            "interrupt_enabled": False,
            "archive_enabled": False,
            "delete_enabled": False,
        },
    }
    state["last_review_id"] = review_id
    state["last_review_at"] = iso_time(now)
    store.save(state)
    rendered = json.dumps(result, indent=2 if args.pretty else None, sort_keys=args.pretty)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


def state_show(args: argparse.Namespace) -> int:
    store = StateStore(Path(args.state_file) if args.state_file else None)
    print(json.dumps(store.load(), indent=2, sort_keys=True))
    return 0


def state_relate(args: argparse.Namespace) -> int:
    store = StateStore(Path(args.state_file) if args.state_file else None)
    state = store.load()
    existing = state["workstreams"].get(args.workstream_id, {})
    state["workstreams"][args.workstream_id] = {
        **existing,
        "title": args.title,
        "canonical_thread_id": args.canonical,
        "related_thread_ids": sorted(
            set(existing.get("related_thread_ids", [])) | set(args.related or [])
        ),
        "status": existing.get("status", "active"),
        "updated_at": iso_time(utc_now()),
    }
    store.save(state)
    return state_show(args)


def state_park(args: argparse.Namespace) -> int:
    store = StateStore(Path(args.state_file) if args.state_file else None)
    state = store.load()
    existing = state["workstreams"].get(args.workstream_id, {})
    state["workstreams"][args.workstream_id] = {
        **existing,
        "title": args.title,
        "canonical_thread_id": args.canonical,
        "related_thread_ids": existing.get("related_thread_ids", []),
        "status": "parked",
        "park": {
            "reason": args.reason,
            "trigger_type": args.trigger_type,
            "trigger_value": args.trigger_value,
            "original_instruction": args.original_instruction,
            "parked_at": iso_time(utc_now()),
            "parked_at_review": state.get("last_review_id"),
        },
        "updated_at": iso_time(utc_now()),
    }
    store.save(state)
    return state_show(args)


def state_change_status(args: argparse.Namespace, status: str) -> int:
    store = StateStore(Path(args.state_file) if args.state_file else None)
    state = store.load()
    workstream = state["workstreams"].get(args.workstream_id)
    if not isinstance(workstream, dict):
        raise ThreadStewardError(f"Unknown workstream: {args.workstream_id}")
    workstream["status"] = status
    if status == "active":
        workstream.pop("park", None)
    workstream["updated_at"] = iso_time(utc_now())
    store.save(state)
    return state_show(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="scan recent and tracked Codex threads read-only")
    scan_parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    scan_parser.add_argument("--max-threads", type=int, default=200)
    scan_parser.add_argument("--timeout", type=float, default=REQUEST_TIMEOUT_SECONDS)
    scan_parser.add_argument("--state-file")
    scan_parser.add_argument("--codex-home")
    scan_parser.add_argument(
        "--current-thread-id",
        default=os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SESSION_ID"),
        help="invoking thread to retain as a relationship anchor but exclude from action categories",
    )
    scan_parser.add_argument("--now", help=argparse.SUPPRESS)
    scan_parser.add_argument("--output")
    scan_parser.add_argument("--pretty", action="store_true")
    scan_parser.set_defaults(handler=scan)

    state_parser = subparsers.add_parser("state", help="manage confirmed local Thread Steward state")
    state_subparsers = state_parser.add_subparsers(dest="state_command", required=True)

    show_parser = state_subparsers.add_parser("show")
    show_parser.add_argument("--state-file")
    show_parser.set_defaults(handler=state_show)

    relate_parser = state_subparsers.add_parser("relate")
    relate_parser.add_argument("--state-file")
    relate_parser.add_argument("--workstream-id", required=True)
    relate_parser.add_argument("--title", required=True)
    relate_parser.add_argument("--canonical", required=True)
    relate_parser.add_argument("--related", action="append", default=[])
    relate_parser.set_defaults(handler=state_relate)

    park_parser = state_subparsers.add_parser("park")
    park_parser.add_argument("--state-file")
    park_parser.add_argument("--workstream-id", required=True)
    park_parser.add_argument("--title", required=True)
    park_parser.add_argument("--canonical", required=True)
    park_parser.add_argument("--reason", required=True)
    park_parser.add_argument(
        "--trigger-type", choices=("next_review", "date", "dependency", "manual"), required=True
    )
    park_parser.add_argument("--trigger-value")
    park_parser.add_argument("--original-instruction", required=True)
    park_parser.set_defaults(handler=state_park)

    resume_parser = state_subparsers.add_parser("resume")
    resume_parser.add_argument("--state-file")
    resume_parser.add_argument("--workstream-id", required=True)
    resume_parser.set_defaults(handler=lambda args: state_change_status(args, "active"))

    close_parser = state_subparsers.add_parser("close")
    close_parser.add_argument("--state-file")
    close_parser.add_argument("--workstream-id", required=True)
    close_parser.set_defaults(handler=lambda args: state_change_status(args, "closed"))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "days", 1) < 1:
        parser.error("--days must be at least 1")
    if getattr(args, "max_threads", 1) < 1:
        parser.error("--max-threads must be at least 1")
    try:
        return args.handler(args)
    except ThreadStewardError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
