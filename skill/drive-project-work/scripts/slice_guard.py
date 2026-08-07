#!/usr/bin/env python3
"""Machine-local slice contracts and Codex lifecycle enforcement.

The state is deliberately outside project repositories. It is a disposable
execution lease, not a product-status authority or acceptance ledger.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


SCHEMA_VERSION = 2
MAX_ACCEPTANCE = 5
MAX_ALLOWED_PATHS = 8
MAX_TEXT = 500
STATE_FOLDER = "drive-project-work"
SLICE_MARKER = "[SLICE_CONTRACT_V1]"

BROAD_OUTCOME_PATTERNS = (
    r"\b(?:complete|finish|implement|deliver|fix|change|refactor)\b.{0,40}\b(?:all|entire|every)\b",
    r"\b(?:all|entire|every)\b.{0,40}\b(?:backlog|project|product|requirements?|features?|work)\b",
    r"\bmust[- ]and[- ]should\b",
    r"\bcontinue\b.{0,30}\b(?:until|through)\b",
    r"\bleave only\b.{0,40}\bunresolved\b",
    r"\bproduction[- ]ready\b",
    r"\b(?:improve|redesign|implement|deliver|build)\b.{0,30}\b(?:every|entire)\b",
    r"\b(?:app|application|project|product|system|platform)\b.{0,15}\b(?:end[- ]to[- ]end|across|overall)\b",
    r"\bevery\s+(?:defect|bug|workflow|screen|journey|module|package)s?\b",
)

IMPLEMENTATION_PROMPT = re.compile(
    r"(?:\$(?:drive-project-work)|\b(?:implement|build|fix|change|finish|complete|ship|refactor|continue)\b)"
    r".*(?:\b(?:project|repo(?:sitory)?|app|application|feature|bug|implementation|backlog|code)\b)",
    re.IGNORECASE | re.DOTALL,
)

EXPLICIT_STOP_PATTERNS = (
    re.compile(r"^\s*(?:please\s+)?(?:stop|pause|wait|hold\s+on)(?:\s+(?:here|there|now|work(?:ing)?|everything|all\s+work)){0,2}[.!\s]*$", re.IGNORECASE),
    re.compile(r"^\s*(?:please\s+)?(?:stop|pause)\s+(?:(?:this|that|current)|the(?:\s+current)?)\s+(?:task|work|process|run)(?:\s+now)?[.!\s]*$", re.IGNORECASE),
    re.compile(r"^\s*(?:please\s+)?stop\s+(?:doing|touching)\s+(?:this|that|anything(?:\s+else)?)[.!\s]*$", re.IGNORECASE),
    re.compile(r"^\s*(?:please\s+)?stop\s+working\s+on\s+(?:this|the|the\s+current)\s+(?:project|task|work)[.!\s]*$", re.IGNORECASE),
    re.compile(r"\bstop immediately\b", re.IGNORECASE),
    re.compile(r"^\s*(?:please\s+)?(?:do\s+not|don['’]?t|dont)\s+(?:continue|keep\s+going|run|edit|start|do|work|touch)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:please\s+)?(?:do\s+not|don['’]?t|dont)\s+make\s+(?:(?:any\s+more|further)\s+)?changes?\b", re.IGNORECASE),
    re.compile(r"\breturn control (?:to me|to the owner)\b", re.IGNORECASE),
)

EXPLICIT_RESUME = re.compile(
    r"^\s*(?:resume|continue|go ahead|proceed|start again)\b",
    re.IGNORECASE,
)

READ_ONLY_SHELL_PATTERNS = (
    r"^\s*(?:rg|where\.exe|Get-Content|Get-ChildItem|Get-Item|Get-FileHash|Get-Command|Select-String|Test-Path|Resolve-Path)\b",
    r"^\s*git\s+(?:-C\s+(?:\"[^\"]+\"|'[^']+'|\S+)\s+)?(?:status|diff|log|show|rev-parse|remote|grep|ls-files|check-ignore|branch\s+--show-current)\b",
)

BROAD_CLAIM_PATTERNS = (
    r"\b(?:the\s+)?(?:project|product|backlog|app|application|system|platform|everything|all\s+(?:of\s+(?:it|this)|work|requirements?))\s+(?:is\s+|are\s+)?(?:complete|completed|done|finished|fixed|implemented|delivered)\b",
    r"\bfully\s+(?:complete|completed|done|implemented|working)\b",
    r"\brelease[- ]ready\b",
    r"\bowner[- ]accepted\b",
    r"\ball\s+(?:requested\s+)?work\s+(?:is\s+)?(?:complete|done|delivered)\b",
    r"\ball\s+requirements?\s+(?:passed|satisfied|met)\b",
    r"\b(?:we\s+are|it\s+is|the\s+product\s+is)\s+ready\s+(?:to|for)\s+(?:release|ship(?:ping)?)\b",
    r"\bship[- ]ready\b",
    r"\bthe\s+requested\s+work\s+(?:is\s+)?(?:now\s+)?(?:complete|completed|done|finished|fixed|delivered)\b",
    r"\bnothing\s+(?:else\s+)?remains(?:\s+to\s+be\s+done)?\b",
    r"\bthere\s+is\s+nothing\s+(?:left|remaining)\b",
    r"(?:^|[.!?]\s+)[A-Z][A-Za-z0-9_-]*\s+(?:is\s+(?:now\s+)?complete|has\s+reached\s+completion)\b",
)

NOISY_IGNORED_ROOTS = {
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "out",
    "target",
}

READ_ONLY_LOCAL_TOOLS = {
    "functions.exec",
    "functions.wait",
    "get_goal",
    "list_agents",
    "list_mcp_resource_templates",
    "list_mcp_resources",
    "read_mcp_resource",
    "request_user_input",
    "update_plan",
    "view_image",
    "wait_agent",
    "web__run",
}

REVIEWER_READ_ONLY_TOOLS = {
    "functions.exec",
    "functions.wait",
    "get_goal",
    "list_agents",
    "list_mcp_resource_templates",
    "list_mcp_resources",
    "read_mcp_resource",
    "view_image",
    "wait_agent",
    "web__run",
}


class GuardError(RuntimeError):
    """A user-facing contract or state error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def state_root() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    base = Path(codex_home) if codex_home else Path.home() / ".codex"
    return base / "state" / STATE_FOLDER / "sessions"


def safe_session_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "_", value.strip())
    if not cleaned:
        raise GuardError("A non-empty Codex session id is required.")
    return cleaned[:180]


def state_path(session_id: str) -> Path:
    return state_root() / f"{safe_session_id(session_id)}.json"


def load_state(session_id: str) -> dict[str, Any] | None:
    path = state_path(session_id)
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GuardError(f"Slice state is unreadable: {type(exc).__name__}.") from exc
    if not isinstance(value, dict):
        raise GuardError("Slice state has an unsupported schema.")
    if value.get("schema_version") == 1:
        value["schema_version"] = SCHEMA_VERSION
        value["status_before_migration"] = value.get("status")
        value["status"] = "migration_required"
        value.setdefault("ignored_baseline", {})
        value.setdefault("goal_requested", False)
        value.setdefault("goal_pending_tool_use_id", None)
        value.setdefault("goal_completion_pending_tool_use_id", None)
        value.setdefault("reviewers_spawned", 0)
        value.setdefault("reviewer_active", False)
        value.setdefault("events", []).append({"at": utc_now(), "type": "schema-migration-required", "from": 1})
        value["updated_at"] = utc_now()
        save_state(value)
    if value.get("schema_version") != SCHEMA_VERSION:
        raise GuardError("Slice state has an unsupported schema.")
    return value


def save_state(state: dict[str, Any]) -> None:
    root = state_root()
    root.mkdir(parents=True, exist_ok=True)
    target = state_path(str(state["session_id"]))
    handle, temporary_name = tempfile.mkstemp(prefix=f".{target.stem}-", suffix=".tmp", dir=root)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(state, stream, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def git_root(cwd: Path) -> Path | None:
    result = subprocess.run(
        ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        encoding="utf-8",
    )
    if result.returncode:
        return None
    return Path(result.stdout.strip()).resolve()


def git_head(cwd: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(cwd), "rev-parse", "HEAD"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        encoding="utf-8",
    )
    return result.stdout.strip() if result.returncode == 0 else None


def file_fingerprint(path: Path, force_hash: bool = False) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    if path.is_dir():
        return {"exists": True, "kind": "directory"}
    stat = path.stat()
    result: dict[str, Any] = {
        "exists": True,
        "kind": "file",
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }
    if force_hash or stat.st_size <= 10 * 1024 * 1024:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        result["sha256"] = digest.hexdigest()
    return result


def parse_porcelain_path(record: str) -> str | None:
    if len(record) < 4:
        return None
    value = record[3:].strip()
    if " -> " in value:
        value = value.split(" -> ", 1)[1]
    if value.startswith('"') and value.endswith('"'):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            value = value[1:-1]
    return value.replace("/", os.sep)


def worktree_snapshot(cwd: Path) -> dict[str, Any]:
    root = git_root(cwd)
    if root is None:
        return {"git_root": None, "git_head": None, "entries": {}}
    result = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    if result.returncode:
        raise GuardError("Could not capture the Git worktree baseline.")
    entries: dict[str, Any] = {}
    for record in result.stdout.splitlines():
        relative = parse_porcelain_path(record)
        if relative:
            entries[relative.replace(os.sep, "/")] = {
                "status": record[:2],
                "fingerprint": file_fingerprint(root / relative),
            }
    return {"git_root": str(root), "git_head": git_head(root), "entries": entries}


def ignored_snapshot(cwd: Path) -> dict[str, Any]:
    root = git_root(cwd)
    if root is None:
        return {}
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--others", "--ignored", "--exclude-standard", "-z"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise GuardError("Could not inspect ignored paths.")
    entries: dict[str, Any] = {}
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        relative = raw.decode("utf-8", "surrogateescape").replace("\\", "/")
        first = relative.split("/", 1)[0].lower()
        if first in NOISY_IGNORED_ROOTS:
            continue
        path = root / relative
        try:
            if path.is_file():
                entries[relative] = file_fingerprint(path)
        except OSError:
            continue
    return entries


def ignored_changes_since_baseline(state: dict[str, Any]) -> list[str]:
    baseline = state.get("ignored_baseline") or {}
    current = ignored_snapshot(Path(state["cwd"]))
    paths = set(baseline) | set(current)
    return sorted(path for path in paths if baseline.get(path) != current.get(path))


def workspace_digest(cwd: Path) -> str:
    value = {
        "worktree": worktree_snapshot(cwd),
        "ignored": ignored_snapshot(cwd),
    }
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def changed_since_baseline(state: dict[str, Any]) -> list[str]:
    baseline = state.get("baseline") or {}
    root_value = baseline.get("git_root")
    if not root_value:
        return []
    current = worktree_snapshot(Path(root_value))
    before = baseline.get("entries") or {}
    after = current.get("entries") or {}
    paths = set(before) | set(after)
    return sorted(path for path in paths if before.get(path) != after.get(path))


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def normalize_allowed_paths(cwd: Path, values: Any) -> list[str]:
    if not isinstance(values, list) or not 1 <= len(values) <= MAX_ALLOWED_PATHS:
        raise GuardError(f"allowed_paths must contain 1 to {MAX_ALLOWED_PATHS} paths.")
    output: list[str] = []
    for raw in values:
        if not isinstance(raw, str) or not raw.strip():
            raise GuardError("Each allowed path must be a non-empty string.")
        candidate = (cwd / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        if candidate == cwd or not is_within(candidate, cwd):
            raise GuardError("Allowed paths must be narrower than and remain inside the project root.")
        relative = candidate.relative_to(cwd).as_posix()
        if len(Path(relative).parts) == 1 and (candidate.is_dir() or not Path(relative).suffix):
            raise GuardError(f"Allowed directory is too broad for one slice: {relative}.")
        if relative not in output:
            output.append(relative)
    return output


def validate_short_text(value: Any, name: str, limit: int = MAX_TEXT) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GuardError(f"{name} must be a non-empty string.")
    cleaned = " ".join(value.split())
    if len(cleaned) > limit:
        raise GuardError(f"{name} must be {limit} characters or fewer.")
    return cleaned


def validate_contract(raw: Any, cwd: Path) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise GuardError("The slice contract must be a JSON object.")
    allowed_keys = {"outcome", "acceptance", "allowed_paths", "outside_scope", "subagents"}
    extra = sorted(set(raw) - allowed_keys)
    if extra:
        raise GuardError(f"Unknown slice contract fields: {', '.join(extra)}.")

    outcome = validate_short_text(raw.get("outcome"), "outcome", 240)
    if any(re.search(pattern, outcome, re.IGNORECASE) for pattern in BROAD_OUTCOME_PATTERNS):
        raise GuardError("Outcome bundles a broad project objective. Choose one user-visible journey.")
    if outcome.count(",") >= 2 or len(re.findall(r"\band\b", outcome, re.IGNORECASE)) >= 3:
        raise GuardError("Outcome reads like a list of journeys. Choose one user-visible journey.")

    acceptance_raw = raw.get("acceptance")
    if not isinstance(acceptance_raw, list) or not 1 <= len(acceptance_raw) <= MAX_ACCEPTANCE:
        raise GuardError(f"acceptance must contain 1 to {MAX_ACCEPTANCE} checks.")
    acceptance: list[dict[str, Any]] = []
    ids: set[str] = set()
    for index, item in enumerate(acceptance_raw, start=1):
        if not isinstance(item, dict):
            raise GuardError("Each acceptance check must be an object.")
        allowed_item_keys = {"id", "kind", "criterion", "command", "timeout_seconds"}
        item_extra = sorted(set(item) - allowed_item_keys)
        if item_extra:
            raise GuardError(f"Unknown acceptance fields: {', '.join(item_extra)}.")
        check_id = str(item.get("id") or f"A{index}").strip().upper()
        if not re.fullmatch(r"A[1-5]", check_id) or check_id in ids:
            raise GuardError("Acceptance ids must be unique A1 through A5 values.")
        ids.add(check_id)
        kind = str(item.get("kind") or "").strip().lower()
        if kind not in {"command", "observe", "owner"}:
            raise GuardError(f"{check_id} kind must be command, observe, or owner.")
        criterion = validate_short_text(item.get("criterion"), f"{check_id} criterion", 280)
        check: dict[str, Any] = {
            "id": check_id,
            "kind": kind,
            "criterion": criterion,
            "status": "pending",
            "evidence": None,
        }
        if kind == "command":
            command = validate_short_text(item.get("command"), f"{check_id} command", 1000)
            timeout = item.get("timeout_seconds", 600)
            if not isinstance(timeout, int) or not 1 <= timeout <= 1800:
                raise GuardError(f"{check_id} timeout_seconds must be 1 through 1800.")
            check["command"] = command
            check["timeout_seconds"] = timeout
        elif "command" in item or "timeout_seconds" in item:
            raise GuardError(f"{check_id} may define a command only when kind is command.")
        acceptance.append(check)
    if all(item["kind"] == "owner" for item in acceptance):
        raise GuardError("At least one acceptance check must be reproducible by Codex.")

    outside_raw = raw.get("outside_scope", [])
    if not isinstance(outside_raw, list) or len(outside_raw) > MAX_ACCEPTANCE:
        raise GuardError(f"outside_scope must be a list of at most {MAX_ACCEPTANCE} items.")
    outside = [validate_short_text(value, "outside_scope item", 240) for value in outside_raw]

    subagents = str(raw.get("subagents") or "none").strip().lower()
    if subagents not in {"none", "reviewer"}:
        raise GuardError("subagents must be none or reviewer. Parallel delivery needs a separate owner-approved workflow.")

    return {
        "outcome": outcome,
        "acceptance": acceptance,
        "allowed_paths": normalize_allowed_paths(cwd, raw.get("allowed_paths")),
        "outside_scope": outside,
        "subagents": subagents,
    }


def goal_objective(state: dict[str, Any]) -> str:
    acceptance = "; ".join(
        f"{item['id']} {item['criterion']}" for item in state["contract"]["acceptance"]
    )
    outside = "; ".join(state["contract"]["outside_scope"]) or "No adjacent work."
    owner = [item["criterion"] for item in state["contract"]["acceptance"] if item["kind"] == "owner"]
    owner_text = "; ".join(owner) or "None."
    return (
        f"{SLICE_MARKER}\n"
        f"Outcome: {state['contract']['outcome']}\n"
        f"Acceptance: {acceptance}\n"
        f"Outside this slice: {outside}\n"
        f"Owner-only gates: {owner_text}\n"
        "Completion boundary: produce a locally verified candidate and report unresolved owner gates; "
        "do not claim whole-project, release, or owner acceptance."
    )


def begin(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).resolve()
    if not cwd.is_dir():
        raise GuardError(f"Project root does not exist: {cwd}")
    root = git_root(cwd)
    if root is None:
        raise GuardError("A guarded implementation slice requires a Git worktree.")
    if root != cwd:
        raise GuardError(f"Use the Git worktree root as --cwd: {root}")
    current = load_state(args.session)
    if current and current.get("status") in {"active", "paused"}:
        raise GuardError("This session already has an unfinished slice. Abort or finish it before replacing it.")
    try:
        raw_contract = json.loads(args.contract)
    except json.JSONDecodeError as exc:
        raise GuardError(f"Contract JSON is invalid: {exc.msg}.") from exc
    contract = validate_contract(raw_contract, cwd)
    baseline = worktree_snapshot(cwd)
    baseline_dirty = [
        path for path in baseline["entries"]
        if path_is_allowed(path, contract["allowed_paths"], cwd)
    ]
    if baseline_dirty:
        raise GuardError(
            "Allowed paths already contain uncommitted work and are not safe to claim as this slice: "
            + ", ".join(baseline_dirty[:12])
        )
    now = utc_now()
    state = {
        "schema_version": SCHEMA_VERSION,
        "session_id": args.session,
        "cwd": str(cwd),
        "created_at": now,
        "updated_at": now,
        "status": "active",
        "goal_status": None,
        "contract": contract,
        "baseline": baseline,
        "ignored_baseline": ignored_snapshot(cwd),
        "goal_requested": False,
        "goal_pending_tool_use_id": None,
        "goal_completion_pending_tool_use_id": None,
        "reviewers_spawned": 0,
        "reviewer_active": False,
        "events": [{"at": now, "type": "begin"}],
    }
    save_state(state)
    print(json.dumps({"status": state["status"], "goal_objective": goal_objective(state)}, indent=2))
    return 0


def require_state(session: str, statuses: set[str] | None = None) -> dict[str, Any]:
    state = load_state(session)
    if state is None:
        raise GuardError("No slice contract exists for this session.")
    if statuses is not None and state.get("status") not in statuses:
        raise GuardError(f"Slice status is {state.get('status')}, expected one of {sorted(statuses)}.")
    return state


def find_check(state: dict[str, Any], check_id: str, kind: str) -> dict[str, Any]:
    wanted = check_id.strip().upper()
    for item in state["contract"]["acceptance"]:
        if item["id"] == wanted:
            if item["kind"] != kind:
                raise GuardError(f"{wanted} is {item['kind']}, not {kind}.")
            return item
    raise GuardError(f"Unknown acceptance check: {wanted}.")


def output_tail(value: str, limit: int = 4000) -> str:
    return value if len(value) <= limit else value[-limit:]


def run_check(args: argparse.Namespace) -> int:
    state = require_state(args.session, {"active"})
    check = find_check(state, args.id, "command")
    cwd = Path(state["cwd"])
    command = check["command"]
    shell = ["powershell", "-NoProfile", "-Command", command] if os.name == "nt" else ["/bin/sh", "-lc", command]
    started = utc_now()
    try:
        result = subprocess.run(
            shell,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
            timeout=check["timeout_seconds"],
        )
        returncode = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired as exc:
        returncode = 124
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTimed out after {check['timeout_seconds']} seconds."
    check["status"] = "pass" if returncode == 0 else "fail"
    check["evidence"] = {
        "kind": "command",
        "started_at": started,
        "finished_at": utc_now(),
        "command": command,
        "returncode": returncode,
        "stdout_sha256": hashlib.sha256(stdout.encode("utf-8", "replace")).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr.encode("utf-8", "replace")).hexdigest(),
        "stdout_tail": output_tail(stdout),
        "stderr_tail": output_tail(stderr),
        "git_head": git_head(cwd),
        "workspace_digest": workspace_digest(cwd),
    }
    state["updated_at"] = utc_now()
    state["events"].append({"at": state["updated_at"], "type": "run-check", "id": check["id"], "result": check["status"]})
    save_state(state)
    if stdout:
        print(output_tail(stdout))
    if stderr:
        print(output_tail(stderr), file=sys.stderr)
    print(json.dumps({"id": check["id"], "status": check["status"], "returncode": returncode}))
    return returncode


def observe(args: argparse.Namespace) -> int:
    state = require_state(args.session, {"active"})
    check = find_check(state, args.id, "observe")
    note = validate_short_text(args.note, "observation note", 600)
    artifacts: list[dict[str, Any]] = []
    if not args.artifact:
        raise GuardError("An observation requires at least one existing artifact path.")
    created = datetime.fromisoformat(state["created_at"].replace("Z", "+00:00")).timestamp()
    for raw in args.artifact:
        path = Path(raw).resolve()
        if not path.is_file():
            raise GuardError(f"Observation artifact does not exist: {path}")
        stat = path.stat()
        if stat.st_mtime < created - 5:
            raise GuardError(f"Observation artifact predates this slice: {path}")
        artifacts.append({"path": str(path), "fingerprint": file_fingerprint(path, force_hash=True)})
    check["status"] = "pass"
    check["evidence"] = {
        "kind": "agent-observed",
        "recorded_at": utc_now(),
        "note": note,
        "artifacts": artifacts,
        "workspace_digest": workspace_digest(Path(state["cwd"])),
    }
    state["updated_at"] = utc_now()
    state["events"].append({"at": state["updated_at"], "type": "observe", "id": check["id"], "result": "pass"})
    save_state(state)
    print(json.dumps({"id": check["id"], "status": "pass", "artifacts": len(artifacts)}))
    return 0


def path_is_allowed(relative: str, allowed_paths: list[str], cwd: Path | None = None) -> bool:
    candidate = Path(relative)
    if cwd is None:
        if candidate.is_absolute() or ".." in candidate.parts:
            return False
        normalized = relative.replace("\\", "/")
        while normalized.startswith("./"):
            normalized = normalized[2:]
    else:
        resolved = candidate.resolve() if candidate.is_absolute() else (cwd / candidate).resolve()
        if not is_within(resolved, cwd):
            return False
        normalized = resolved.relative_to(cwd).as_posix()
    for allowed in allowed_paths:
        if normalized == allowed or normalized.startswith(allowed.rstrip("/") + "/"):
            return True
    return False


def candidate(args: argparse.Namespace) -> int:
    state = require_state(args.session, {"active"})
    non_owner = [item for item in state["contract"]["acceptance"] if item["kind"] != "owner"]
    failures = [item["id"] for item in non_owner if item["status"] == "fail"]
    pending = [item["id"] for item in non_owner if item["status"] != "pass"]
    if failures or pending:
        details = []
        if failures:
            details.append(f"failed: {', '.join(failures)}")
        if pending:
            details.append(f"not passed: {', '.join(pending)}")
        raise GuardError("Candidate gate is not satisfied (" + "; ".join(details) + ").")
    current_digest = workspace_digest(Path(state["cwd"]))
    stale = [
        item["id"] for item in non_owner
        if (item.get("evidence") or {}).get("workspace_digest") != current_digest
    ]
    if stale:
        raise GuardError(
            "Acceptance evidence predates the current worktree. Re-run or re-observe: "
            + ", ".join(stale)
        )
    stale_artifacts: list[str] = []
    for item in non_owner:
        evidence = item.get("evidence") or {}
        if evidence.get("kind") != "agent-observed":
            continue
        for artifact in evidence.get("artifacts") or []:
            path = Path(str(artifact.get("path") or ""))
            if file_fingerprint(path, force_hash=True) != artifact.get("fingerprint"):
                stale_artifacts.append(f"{item['id']}:{path}")
    if stale_artifacts:
        raise GuardError(
            "Observed artifacts changed or disappeared after inspection. Re-observe: "
            + ", ".join(stale_artifacts[:8])
        )
    current_snapshot = worktree_snapshot(Path(state["cwd"]))
    if current_snapshot.get("git_head") != (state.get("baseline") or {}).get("git_head"):
        raise GuardError("Git HEAD changed during the slice. Delivery and history changes require a separate owner-approved step.")
    changed = changed_since_baseline(state)
    ignored = ignored_changes_since_baseline(state)
    outside = [path for path in changed + ignored if not path_is_allowed(path, state["contract"]["allowed_paths"])]
    if outside:
        raise GuardError("Paths changed outside the slice lease: " + ", ".join(outside[:12]))
    all_changed = sorted(set(changed + ignored))
    allowed_changed = [path for path in all_changed if path_is_allowed(path, state["contract"]["allowed_paths"])]
    if not allowed_changed:
        raise GuardError("No allowed project path changed. Report a clean no-op instead of a delivery candidate.")
    owner = [item for item in state["contract"]["acceptance"] if item["kind"] == "owner"]
    observed = [item for item in state["contract"]["acceptance"] if item["kind"] == "observe"]
    owner_gates = [item["criterion"] for item in owner]
    owner_gates.extend(f"Independent acceptance of agent-observed {item['id']}: {item['criterion']}" for item in observed)
    state["status"] = "candidate_needs_owner" if owner_gates else "candidate_ready"
    state["updated_at"] = utc_now()
    state["candidate"] = {
        "at": state["updated_at"],
        "git_head": git_head(Path(state["cwd"])),
        "changed_paths": all_changed,
        "owner_gates": owner_gates,
    }
    state["events"].append({"at": state["updated_at"], "type": "candidate", "status": state["status"]})
    save_state(state)
    print(json.dumps({
        "status": state["status"],
        "outcome": state["contract"]["outcome"],
        "changed_paths": all_changed,
        "owner_gates": state["candidate"]["owner_gates"],
        "claim_boundary": "Candidate only. This does not establish whole-project, release, or owner acceptance.",
    }, indent=2))
    return 0


def abort(args: argparse.Namespace) -> int:
    state = require_state(args.session)
    if state.get("status") in {"candidate_ready", "candidate_needs_owner", "aborted"}:
        raise GuardError(f"Slice is already terminal: {state.get('status')}.")
    reason = validate_short_text(args.reason, "abort reason", 500)
    state["status"] = "aborted"
    state["updated_at"] = utc_now()
    state["events"].append({"at": state["updated_at"], "type": "abort", "reason": reason})
    save_state(state)
    print(json.dumps({"status": "aborted", "reason": reason}))
    return 0


def print_status(args: argparse.Namespace) -> int:
    state = load_state(args.session)
    if state is None:
        print(json.dumps({"status": "none", "session_id": args.session}))
        return 0
    print(json.dumps({
        "status": state.get("status"),
        "goal_status": state.get("goal_status"),
        "outcome": (state.get("contract") or {}).get("outcome"),
        "allowed_paths": (state.get("contract") or {}).get("allowed_paths", []),
        "acceptance": [
            {"id": item["id"], "kind": item["kind"], "status": item["status"], "criterion": item["criterion"]}
            for item in (state.get("contract") or {}).get("acceptance", [])
        ],
        "outside_scope": (state.get("contract") or {}).get("outside_scope", []),
    }, indent=2))
    return 0


def hook_response(event: str, **values: Any) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, **values}}))


def deny(event: str, reason: str) -> int:
    hook_response(event, permissionDecision="deny", permissionDecisionReason=reason)
    return 0


def command_matches_any(command: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, command, re.IGNORECASE | re.MULTILINE) for pattern in patterns)


def is_read_only_command(command: str) -> bool:
    if has_unquoted_shell_control(command):
        return False
    if not command_matches_any(command, READ_ONLY_SHELL_PATTERNS):
        return False
    if re.search(r"\b(?:Set|Add|Remove|Move|Copy|Rename|New)-(?:Item|Content)\b", command, re.IGNORECASE):
        return False
    if re.search(r"(?:^|\s)--(?:pre(?:-glob)?|ext-diff|output)(?:=|\s|$)", command, re.IGNORECASE):
        return False
    return True


def tool_matches(tool: str, names: set[str]) -> bool:
    normalized = tool.strip().lower()
    candidates = {normalized, normalized.rsplit(".", 1)[-1]}
    return bool(candidates & {name.lower() for name in names})


def has_unquoted_shell_control(command: str) -> bool:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(command):
        if character in "\r\n":
            return True
        if escaped:
            escaped = False
            continue
        if (os.name == "nt" and character == "`") or (os.name != "nt" and character == "\\"):
            escaped = True
            continue
        if quote:
            if character == quote:
                quote = None
            continue
        if character in {"'", '"'}:
            quote = character
            continue
        if character in ";|&<>(){}":
            return True
        if character == "$" and index + 1 < len(command) and command[index + 1] == "(":
            return True
    return quote is not None


def shell_tokens(command: str) -> list[str] | None:
    if has_unquoted_shell_control(command):
        return None
    tokens: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    for character in command:
        if escaped:
            current.append(character)
            escaped = False
            continue
        if (os.name == "nt" and character == "`") or (os.name != "nt" and character == "\\"):
            escaped = True
            continue
        if quote:
            if character == quote:
                quote = None
            else:
                current.append(character)
            continue
        if character in {"'", '"'}:
            quote = character
        elif character.isspace():
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(character)
    if quote or escaped:
        return None
    if current:
        tokens.append("".join(current))
    return tokens


def same_resolved_path(left: str, right: Path) -> bool:
    try:
        return os.path.normcase(str(Path(left).resolve())) == os.path.normcase(str(right.resolve()))
    except OSError:
        return False


def guard_command_action(command: str, expected_session: str, expected_cwd: Path) -> str | None:
    tokens = shell_tokens(command)
    if not tokens:
        return None
    index = 0
    launcher = Path(tokens[0]).name.lower()
    if launcher in {"py", "py.exe"}:
        if len(tokens) < 4 or tokens[1] != "-3":
            return None
        index = 2
    elif same_resolved_path(tokens[0], Path(sys.executable)):
        if len(tokens) < 3:
            return None
        index = 1
    else:
        return None
    if not same_resolved_path(tokens[index], Path(__file__)):
        return None
    if index + 1 >= len(tokens):
        return None
    action = tokens[index + 1].lower()
    args = tokens[index + 2:]
    if action in {"candidate", "status"}:
        valid = args == ["--session", expected_session]
    elif action == "run-check":
        valid = len(args) == 4 and args[:2] == ["--session", expected_session] and args[2] == "--id" and bool(re.fullmatch(r"A[1-5]", args[3], re.IGNORECASE))
    elif action == "observe":
        valid = (
            len(args) >= 8
            and args[:2] == ["--session", expected_session]
            and args[2] == "--id"
            and bool(re.fullmatch(r"A[1-5]", args[3], re.IGNORECASE))
            and args[4] == "--note"
            and all(args[position] == "--artifact" for position in range(6, len(args), 2))
            and len(args[6:]) % 2 == 0
        )
    elif action == "abort":
        valid = len(args) == 4 and args[:2] == ["--session", expected_session] and args[2] == "--reason"
    elif action == "begin":
        valid = (
            len(args) == 6
            and args[:2] == ["--session", expected_session]
            and args[2] == "--cwd"
            and same_resolved_path(args[3], expected_cwd)
            and args[4] == "--contract"
        )
    else:
        valid = False
    return action if valid else None


def patch_paths(command: str) -> list[str]:
    paths: list[str] = []
    for line in command.splitlines():
        match = re.match(r"\*\*\* (?:Add|Update|Delete) File: (.+)$", line)
        if match:
            paths.append(match.group(1).strip())
        move = re.match(r"\*\*\* Move to: (.+)$", line)
        if move:
            paths.append(move.group(1).strip())
    return paths


def normalized_goal(value: str) -> str:
    return " ".join(value.split())


def status_context(payload: dict[str, Any], state: dict[str, Any] | None) -> str:
    session_id = str(payload.get("session_id") or "")
    script = Path(__file__).resolve()
    if state is None:
        return (
            "Project slice guard is available for consequential implementation. "
            f"Current session id: {session_id}. Before the first project mutation, use $drive-project-work "
            f"and establish one bounded slice with `{sys.executable} \"{script}\" begin ...`. "
            "This is unnecessary for read-only answers."
        )
    if state.get("status") == "migration_required":
        return (
            "Project slice guard found older execution state and failed closed. "
            f"Use `{sys.executable} \"{script}\" abort --session \"{session_id}\" --reason \"Discard incompatible prior guard state\"`, "
            "then establish a new bounded slice. Do not continue implementation against migrated evidence."
        )
    contract = state.get("contract") or {}
    checks = ", ".join(f"{item['id']}={item['status']}" for item in contract.get("acceptance", [])) or "none"
    return (
        f"Active machine-local slice guard: status={state.get('status')}; outcome={contract.get('outcome')}; "
        f"checks={checks}; allowed_paths={contract.get('allowed_paths', [])}. "
        "Do not transition scope or broaden the completion claim."
    )


def pre_tool_use(payload: dict[str, Any], state: dict[str, Any] | None) -> int:
    event = "PreToolUse"
    tool = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "") if isinstance(tool_input, dict) else ""
    session_id = str(payload.get("session_id") or (state or {}).get("session_id") or "")
    tool_workdir = tool_input.get("workdir") if isinstance(tool_input, dict) else None
    expected_cwd = Path(tool_workdir or payload.get("cwd") or (state or {}).get("cwd") or Path.cwd()).resolve()
    guard_action = guard_command_action(command, session_id, expected_cwd) if command else None

    if state and state.get("status") == "paused":
        if guard_action == "status":
            return 0
        return deny(event, "Owner stop latch is active. No more tools may run until the owner explicitly says resume or proceed.")

    if state and state.get("reviewer_active"):
        if guard_action == "status":
            return 0
        if command and is_read_only_command(command):
            return 0
        if not command and tool_matches(tool, REVIEWER_READ_ONLY_TOOLS):
            return 0
        return deny(event, "The bounded reviewer is active and read-only. Wait for SubagentStop before any mutation or coordination call.")

    if tool_matches(tool, {"create_goal"}):
        objective = str(tool_input.get("objective") or "") if isinstance(tool_input, dict) else ""
        project_goal = bool(re.search(r"\b(?:implement|build|fix|complete|finish|deliver|ship|refactor)\b", objective, re.IGNORECASE))
        if state is None and not project_goal and not objective.startswith(SLICE_MARKER):
            return 0
        if not state or state.get("status") != "active":
            return deny(event, "Project implementation goals require an active bounded slice contract first.")
        if normalized_goal(objective) != normalized_goal(goal_objective(state)):
            return deny(event, "Goal objective does not exactly match the active slice contract and its candidate-only boundary.")
        if state.get("goal_requested") or state.get("goal_pending_tool_use_id"):
            return deny(event, "This slice already requested its one exact guarded Goal.")
        tool_use_id = str(payload.get("tool_use_id") or "")
        if not tool_use_id:
            return deny(event, "Goal creation is missing a tool-use id, so success cannot be confirmed after the call.")
        state["goal_pending_tool_use_id"] = tool_use_id
        state["updated_at"] = utc_now()
        state["events"].append({"at": state["updated_at"], "type": "goal-request-pending"})
        save_state(state)
        return 0

    if tool_matches(tool, {"update_goal"}):
        requested = str(tool_input.get("status") or "") if isinstance(tool_input, dict) else ""
        if requested != "complete" or state is None:
            return 0
        if not state.get("goal_requested"):
            return deny(event, "No exact guarded Goal was requested for this slice, so Goal completion cannot be claimed.")
        if state.get("status") not in {"candidate_ready", "candidate_needs_owner"}:
            return deny(event, "Goal completion is blocked until the slice guard records a candidate-ready state.")
        tool_use_id = str(payload.get("tool_use_id") or "")
        if not tool_use_id:
            return deny(event, "Goal completion is missing a tool-use id, so success cannot be confirmed after the call.")
        state["goal_completion_pending_tool_use_id"] = tool_use_id
        state["updated_at"] = utc_now()
        state["events"].append({"at": state["updated_at"], "type": "goal-completion-pending"})
        save_state(state)
        return 0

    if tool in {"followup_task", "collaboration.followup_task", "send_message", "collaboration.send_message"}:
        if state is not None:
            return deny(event, "Worker re-tasking or follow-up messaging is outside this one-request reviewer boundary.")
        return 0

    if tool in {"Agent", "spawn_agent", "collaboration.spawn_agent"}:
        if state is None:
            return 0
        mode = (state.get("contract") or {}).get("subagents", "none")
        if state.get("status") == "contract_required" or mode == "none":
            return deny(event, "Subagent fan-out is outside the active slice lease.")
        message = str(tool_input.get("message") or "") if isinstance(tool_input, dict) else ""
        if mode == "reviewer":
            if state.get("reviewers_spawned", 0) >= 1:
                return deny(event, "The slice allows one fresh-context reviewer, not an open-ended review loop.")
            if not re.search(r"\b(?:review|counterexample|acceptance)\b", message, re.IGNORECASE) or not re.search(r"\bread[- ]only\b", message, re.IGNORECASE):
                return deny(event, "The allowed subagent must be a bounded read-only acceptance reviewer.")
            state["reviewers_spawned"] = 1
            state["updated_at"] = utc_now()
            save_state(state)
        return 0

    if tool == "apply_patch":
        if state is None or state.get("status") == "contract_required":
            return deny(event, "Start one bounded slice contract before editing project files.")
        if state.get("status") != "active":
            return deny(event, f"Project edits are blocked while slice status is {state.get('status')}.")
        paths = patch_paths(command)
        if not paths:
            return deny(event, "Could not resolve apply_patch targets against the active slice lease.")
        allowed = state["contract"]["allowed_paths"]
        outside = [path for path in paths if not path_is_allowed(path, allowed, Path(state["cwd"]))]
        if outside:
            return deny(event, "Patch targets outside the active slice lease: " + ", ".join(outside))
        return 0

    if not command:
        if state is None or tool_matches(tool, READ_ONLY_LOCAL_TOOLS):
            return 0
        return deny(event, "Unclassified structured local tool blocked by the slice lease. Only the explicit read-only tool allowlist may run.")

    if state is None:
        return 0

    if guard_action:
        return 0
    status = state.get("status")
    if status not in {"active", "candidate_ready", "candidate_needs_owner"}:
        if status != "contract_required":
            return deny(event, f"Command work is blocked while slice status is {status}.")
    if is_read_only_command(command):
        return 0
    return deny(
        event,
        "Unclassified command blocked by the slice lease. Use read-only inspection, scoped apply_patch, or an exact declared slice_guard.py command.",
    )


def goal_tool_succeeded(response: Any, expected_status: str) -> bool:
    if not isinstance(response, dict) or response.get("isError") is True or response.get("error"):
        return False
    candidates = [response]
    for key in ("structuredContent", "goal"):
        nested = response.get(key)
        if isinstance(nested, dict):
            candidates.append(nested)
            goal = nested.get("goal")
            if isinstance(goal, dict):
                candidates.append(goal)
    return any(str(candidate.get("status") or "").lower() == expected_status for candidate in candidates)


def post_tool_use(payload: dict[str, Any], state: dict[str, Any] | None) -> int:
    if state is None:
        print("{}")
        return 0
    tool = str(payload.get("tool_name") or "")
    tool_use_id = str(payload.get("tool_use_id") or "")
    tool_input = payload.get("tool_input") or {}
    response = payload.get("tool_response")
    if tool_matches(tool, {"create_goal"}) and state.get("goal_pending_tool_use_id") == tool_use_id:
        objective = str(tool_input.get("objective") or "") if isinstance(tool_input, dict) else ""
        succeeded = goal_tool_succeeded(response, "active") and normalized_goal(objective) == normalized_goal(goal_objective(state))
        state["goal_pending_tool_use_id"] = None
        state["goal_requested"] = succeeded
        state["updated_at"] = utc_now()
        state["events"].append({"at": state["updated_at"], "type": "goal-request-result", "result": "success" if succeeded else "failure"})
        save_state(state)
        hook_response("PostToolUse", additionalContext="Exact guarded Goal creation confirmed." if succeeded else "Goal creation was not confirmed; Goal completion remains blocked.")
        return 0
    if tool_matches(tool, {"update_goal"}) and state.get("goal_completion_pending_tool_use_id") == tool_use_id:
        requested = str(tool_input.get("status") or "") if isinstance(tool_input, dict) else ""
        succeeded = requested == "complete" and goal_tool_succeeded(response, "complete")
        state["goal_completion_pending_tool_use_id"] = None
        state["goal_status"] = "complete" if succeeded else state.get("goal_status")
        state["updated_at"] = utc_now()
        state["events"].append({"at": state["updated_at"], "type": "goal-completion-result", "result": "success" if succeeded else "failure"})
        save_state(state)
        hook_response("PostToolUse", additionalContext="Guarded Goal completion confirmed." if succeeded else "Goal completion was not confirmed; do not claim it changed.")
        return 0
    print("{}")
    return 0


def user_prompt_submit(payload: dict[str, Any], state: dict[str, Any] | None) -> int:
    prompt = str(payload.get("prompt") or "")
    session_id = str(payload.get("session_id") or "")
    cwd = str(Path(payload.get("cwd") or Path.cwd()).resolve())
    if any(pattern.search(prompt) for pattern in EXPLICIT_STOP_PATTERNS):
        if state is None:
            now = utc_now()
            state = {
                "schema_version": SCHEMA_VERSION,
                "session_id": session_id,
                "cwd": cwd,
                "created_at": now,
                "updated_at": now,
                "status": "paused",
                "goal_status": None,
                "contract": None,
                "baseline": {"git_root": None, "entries": {}},
                "ignored_baseline": {},
                "goal_requested": False,
                "goal_pending_tool_use_id": None,
                "goal_completion_pending_tool_use_id": None,
                "reviewers_spawned": 0,
                "reviewer_active": False,
                "events": [],
            }
        state["status_before_pause"] = state.get("status") if state.get("status") != "paused" else state.get("status_before_pause", "active")
        state["status"] = "paused"
        state["updated_at"] = utc_now()
        state["events"].append({"at": state["updated_at"], "type": "owner-stop"})
        save_state(state)
        hook_response("UserPromptSubmit", additionalContext="OWNER STOP LATCH ACTIVE. Return a concise status only. Do not call tools or continue queued work.")
        return 0
    if state and state.get("status") == "paused":
        if EXPLICIT_RESUME.search(prompt):
            restored = state.get("status_before_pause") or ("active" if state.get("contract") else "contract_required")
            state["status"] = restored
            state["updated_at"] = utc_now()
            state["events"].append({"at": state["updated_at"], "type": "owner-resume"})
            save_state(state)
            hook_response("UserPromptSubmit", additionalContext=f"Owner explicitly resumed work. Restored slice status: {restored}.")
        else:
            hook_response("UserPromptSubmit", additionalContext="Owner stop latch remains active. Answer without tools; require an explicit resume, continue, go ahead, or proceed before acting.")
        return 0
    if state is None and IMPLEMENTATION_PROMPT.search(prompt):
        now = utc_now()
        required = {
            "schema_version": SCHEMA_VERSION,
            "session_id": session_id,
            "cwd": cwd,
            "created_at": now,
            "updated_at": now,
            "status": "contract_required",
            "goal_status": None,
            "contract": None,
            "baseline": {"git_root": None, "entries": {}},
            "ignored_baseline": {},
            "goal_requested": False,
            "goal_pending_tool_use_id": None,
            "goal_completion_pending_tool_use_id": None,
            "reviewers_spawned": 0,
            "reviewer_active": False,
            "events": [{"at": now, "type": "contract-required"}],
        }
        save_state(required)
        hook_response(
            "UserPromptSubmit",
            additionalContext=(
                "This implementation request requires $drive-project-work. Establish one bounded slice contract before mutation. "
                "Do not turn the broader objective into a completion claim."
            ),
        )
    return 0


def subagent_start(payload: dict[str, Any], state: dict[str, Any] | None) -> int:
    if (
        state
        and (state.get("contract") or {}).get("subagents") == "reviewer"
        and state.get("reviewers_spawned") == 1
    ):
        state["reviewer_active"] = True
        state["updated_at"] = utc_now()
        state["events"].append({"at": state["updated_at"], "type": "reviewer-start"})
        save_state(state)
        hook_response(
            "SubagentStart",
            additionalContext=(
                "READ-ONLY REVIEWER LEASE. Inspect the supplied contract, diff, and artifacts for one bounded "
                "counterexample review. Do not edit, run verification, delegate, or broaden the project audit."
            ),
        )
    else:
        print("{}")
    return 0


def subagent_stop(payload: dict[str, Any], state: dict[str, Any] | None) -> int:
    if state and state.get("reviewer_active"):
        state["reviewer_active"] = False
        state["updated_at"] = utc_now()
        state["events"].append({"at": state["updated_at"], "type": "reviewer-stop"})
        save_state(state)
        hook_response("SubagentStop", additionalContext="The one bounded reviewer has returned. Resolve its load-bearing findings once; do not launch another review loop.")
    else:
        print("{}")
    return 0


def stop_hook(payload: dict[str, Any], state: dict[str, Any] | None) -> int:
    if state is None:
        print("{}")
        return 0
    status = state.get("status")
    message = str(payload.get("last_assistant_message") or "")
    already_continued = bool(payload.get("stop_hook_active"))
    broad_claim = command_matches_any(message, BROAD_CLAIM_PATTERNS)
    goal_complete_claim = bool(re.search(r"\bgoal\b.{0,25}\b(?:marked\s+complete|is\s+complete|was\s+completed)\b", message, re.IGNORECASE))
    reason = ""
    if broad_claim:
        reason = "The slice lease cannot support whole-project, all-requirements, release-ready, or owner-accepted language. Remove that claim."
    elif goal_complete_claim and state.get("goal_status") != "complete":
        reason = "The handoff claims Goal state changed, but no successful guarded Goal completion was recorded. Remove or correct that claim."
    elif status == "contract_required":
        if re.search(r"\b(?:done|complete|completed|finished|ready|implemented|fixed|delivered)\b", message, re.IGNORECASE):
            reason = "No slice contract or acceptance evidence exists. Correct the handoff to say that no candidate was established."
    elif status == "active":
        allowed = re.search(r"^Status:\s*(?:Active slice incomplete|Blocked|Needs owner decision)\s*$", message, re.IGNORECASE | re.MULTILINE)
        if not allowed:
            reason = "The active slice is not candidate-ready. Use an honest status line: Active slice incomplete, Blocked, or Needs owner decision."
    elif status == "paused":
        if not re.search(r"^Status:\s*Paused by owner\s*$", message, re.IGNORECASE | re.MULTILINE):
            reason = "The owner paused work. Return only a concise status with `Status: Paused by owner`."
    elif status == "migration_required":
        if not re.search(r"^Status:\s*Blocked\s*$", message, re.IGNORECASE | re.MULTILINE):
            reason = "Older guard state failed closed. Use `Status: Blocked`, abort that state, and establish a fresh slice contract."
    elif status in {"candidate_ready", "candidate_needs_owner"}:
        required = "Candidate needs owner acceptance" if status == "candidate_needs_owner" else "Candidate ready"
        if not re.search(rf"^Status:\s*{re.escape(required)}\s*$", message, re.IGNORECASE | re.MULTILINE):
            reason = f"Use the exact bounded status line `Status: {required}` and state remaining gates."
    if reason and not already_continued:
        print(json.dumps({"decision": "block", "reason": reason}))
    elif reason:
        print(json.dumps({"systemMessage": reason}))
    else:
        print("{}")
    return 0


def hook_main() -> int:
    payload = json.load(sys.stdin)
    event = str(payload.get("hook_event_name") or "")
    session_id = str(payload.get("session_id") or "")
    state = load_state(session_id) if session_id else None
    if event == "SessionStart":
        hook_response(event, additionalContext=status_context(payload, state))
        return 0
    if event == "UserPromptSubmit":
        return user_prompt_submit(payload, state)
    if event == "PreToolUse":
        return pre_tool_use(payload, state)
    if event == "PostToolUse":
        return post_tool_use(payload, state)
    if event == "SubagentStart":
        return subagent_start(payload, state)
    if event == "SubagentStop":
        return subagent_stop(payload, state)
    if event == "Stop":
        return stop_hook(payload, state)
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Manage one machine-local project slice lease.")
    subparsers = result.add_subparsers(dest="action", required=True)

    hook_parser = subparsers.add_parser("hook", help="Read one Codex hook event from stdin.")
    hook_parser.set_defaults(handler=lambda _args: hook_main())

    begin_parser = subparsers.add_parser("begin", help="Validate and start one bounded slice.")
    begin_parser.add_argument("--session", required=True)
    begin_parser.add_argument("--cwd", required=True)
    begin_parser.add_argument("--contract", required=True)
    begin_parser.set_defaults(handler=begin)

    run_parser = subparsers.add_parser("run-check", help="Run one declared command check and record its result.")
    run_parser.add_argument("--session", required=True)
    run_parser.add_argument("--id", required=True)
    run_parser.set_defaults(handler=run_check)

    observe_parser = subparsers.add_parser("observe", help="Record a declared observation with current artifacts.")
    observe_parser.add_argument("--session", required=True)
    observe_parser.add_argument("--id", required=True)
    observe_parser.add_argument("--note", required=True)
    observe_parser.add_argument("--artifact", action="append")
    observe_parser.set_defaults(handler=observe)

    candidate_parser = subparsers.add_parser("candidate", help="Check scope and produce a bounded candidate receipt.")
    candidate_parser.add_argument("--session", required=True)
    candidate_parser.set_defaults(handler=candidate)

    status_parser = subparsers.add_parser("status", help="Show the current slice without changing it.")
    status_parser.add_argument("--session", required=True)
    status_parser.set_defaults(handler=print_status)

    abort_parser = subparsers.add_parser("abort", help="Abort the active slice with a reason.")
    abort_parser.add_argument("--session", required=True)
    abort_parser.add_argument("--reason", required=True)
    abort_parser.set_defaults(handler=abort)
    return result


def main() -> int:
    try:
        args = parser().parse_args()
        return int(args.handler(args))
    except GuardError as exc:
        print(f"slice-guard: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"slice-guard: hook input is invalid JSON: {exc.msg}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"slice-guard: unexpected {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
