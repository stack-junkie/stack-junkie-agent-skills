#!/usr/bin/env python3
"""Install drive-project-work hooks without replacing unrelated user hooks."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import tempfile
from typing import Any


MANAGED_TOKENS = (
    "hooks/drive_project_work_hook.py",
    "drive-project-work/scripts/slice_guard.py",
)


def normalized_command(value: Any) -> str:
    return str(value or "").replace("\\", "/").lower()


def is_managed_handler(handler: Any) -> bool:
    if not isinstance(handler, dict):
        return False
    command = normalized_command(handler.get("command"))
    command_windows = normalized_command(handler.get("commandWindows"))
    return any(token in command or token in command_windows for token in MANAGED_TOKENS)


def remove_managed_groups(config: dict[str, Any]) -> None:
    hooks = config.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("hooks.json `hooks` must be an object")
    for event, groups in list(hooks.items()):
        if not isinstance(groups, list):
            raise ValueError(f"hooks.json event {event} must be an array")
        retained = []
        for group in groups:
            if not isinstance(group, dict):
                retained.append(group)
                continue
            handlers = group.get("hooks")
            if isinstance(handlers, list) and any(is_managed_handler(handler) for handler in handlers):
                remaining = [handler for handler in handlers if not is_managed_handler(handler)]
                if remaining:
                    updated = dict(group)
                    updated["hooks"] = remaining
                    retained.append(updated)
            else:
                retained.append(group)
        if retained:
            hooks[event] = retained
        else:
            hooks.pop(event, None)


def handler(command: str, command_windows: str, status: str, context_limit: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "type": "command",
        "command": command,
        "commandWindows": command_windows,
        "timeout": 30,
        "statusMessage": status,
    }
    if context_limit is not None:
        result["additionalContextLimit"] = context_limit
    return result


def managed_groups(hook_script: Path) -> dict[str, list[dict[str, Any]]]:
    posix_command = f"python3 {shlex.quote(str(hook_script))}"
    windows_command = f'py -3 "{hook_script}"'
    return {
        "SessionStart": [{
            "matcher": "startup|resume|clear|compact",
            "hooks": [handler(posix_command, windows_command, "Loading the active project slice", 900)],
        }],
        "UserPromptSubmit": [{
            "hooks": [handler(posix_command, windows_command, "Checking owner stop and slice boundaries", 700)],
        }],
        "PreToolUse": [{
            "matcher": "*",
            "hooks": [handler(posix_command, windows_command, "Checking the active project slice")],
        }],
        "PostToolUse": [{
            "matcher": "create_goal|update_goal",
            "hooks": [handler(posix_command, windows_command, "Confirming guarded Goal state", 500)],
        }],
        "SubagentStart": [{
            "matcher": "*",
            "hooks": [handler(posix_command, windows_command, "Starting the bounded read-only reviewer", 700)],
        }],
        "SubagentStop": [{
            "matcher": "*",
            "hooks": [handler(posix_command, windows_command, "Closing the bounded reviewer", 700)],
        }],
        "Stop": [{
            "hooks": [handler(posix_command, windows_command, "Checking the completion claim")],
        }],
    }


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "description": "User lifecycle hooks, including the machine-local project slice guard.",
            "hooks": {},
        }
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("hooks.json root must be an object")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=".hooks-", suffix=".json.tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
        json.loads(temporary.read_text(encoding="utf-8"))
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex-home", required=True)
    parser.add_argument("--hook-script", required=True)
    args = parser.parse_args()

    codex_home = Path(args.codex_home).resolve()
    hook_script = Path(args.hook_script).resolve()
    if not hook_script.is_file():
        raise SystemExit(f"Hook script not found: {hook_script}")
    hooks_path = codex_home / "hooks.json"
    config = load_config(hooks_path)
    remove_managed_groups(config)
    hooks = config.setdefault("hooks", {})
    for event, groups in managed_groups(hook_script).items():
        hooks.setdefault(event, []).extend(groups)
    atomic_write(hooks_path, config)
    print(f"[install] Merged drive-project-work lifecycle hooks into {hooks_path}")
    print("[install] Codex will skip changed hooks until the owner reviews and trusts them with /hooks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
