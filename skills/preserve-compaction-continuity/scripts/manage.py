#!/usr/bin/env python3
"""Preview, install, inspect, or remove the Codex continuity skill."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shlex
import shutil
from pathlib import Path
from typing import Any


SKILL_NAME = "preserve-compaction-continuity"
STATUS_MESSAGES = {
    "Preserving the full recovery packet",
    "Rehydrating exact owner context",
}


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".codex").resolve()


def skill_source() -> Path:
    return Path(__file__).resolve().parents[1]


def targets() -> dict[str, Path]:
    home = codex_home()
    return {
        "home": home,
        "skill": home / "skills" / SKILL_NAME,
        "runtime": home / "hooks" / "continuity_recovery.py",
        "hooks": home / "hooks.json",
        "backups": home / "backups" / SKILL_NAME,
    }


def _hash_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _file_manifest(root: Path) -> dict[str, str]:
    if not root.is_dir():
        return {}
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        result[path.relative_to(root).as_posix()] = _hash_bytes(path.read_bytes())
    return result


def _read_hooks(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"description": "User-wide Codex hooks.", "hooks": {}}
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("hooks.json must contain a JSON object")
    hooks = parsed.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("hooks.json field 'hooks' must be an object")
    return parsed


def _is_managed_handler(handler: Any, runtime: Path) -> bool:
    if not isinstance(handler, dict):
        return False
    commands = f"{handler.get('command', '')}\n{handler.get('commandWindows', '')}".lower()
    runtime_text = str(runtime).replace("\\", "/").lower()
    normalized_commands = commands.replace("\\", "/")
    return runtime_text in normalized_commands or (
        "continuity_recovery.py" in normalized_commands
        and handler.get("statusMessage") in STATUS_MESSAGES
    )


def _remove_managed(data: dict[str, Any], runtime: Path) -> bool:
    changed = False
    hooks = data.setdefault("hooks", {})
    for event in ("PreCompact", "SessionStart"):
        groups = hooks.get(event)
        if not isinstance(groups, list):
            continue
        retained_groups: list[Any] = []
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                retained_groups.append(group)
                continue
            retained_handlers = [
                item for item in group["hooks"] if not _is_managed_handler(item, runtime)
            ]
            if len(retained_handlers) != len(group["hooks"]):
                changed = True
            if retained_handlers:
                copy = dict(group)
                copy["hooks"] = retained_handlers
                retained_groups.append(copy)
        if retained_groups:
            hooks[event] = retained_groups
        elif event in hooks:
            del hooks[event]
            changed = True
    return changed


def _managed_handlers(runtime: Path) -> dict[str, dict[str, Any]]:
    posix_command = f"python3 {shlex.quote(str(runtime))}"
    windows_command = f'py -3 "{runtime}"'
    return {
        "PreCompact": {
            "matcher": "manual|auto",
            "hooks": [
                {
                    "type": "command",
                    "command": posix_command,
                    "commandWindows": windows_command,
                    "timeout": 30,
                    "statusMessage": "Preserving the full recovery packet",
                }
            ],
        },
        "SessionStart": {
            "matcher": "compact|resume",
            "hooks": [
                {
                    "type": "command",
                    "command": posix_command,
                    "commandWindows": windows_command,
                    "timeout": 30,
                    "statusMessage": "Rehydrating exact owner context",
                    "additionalContextLimit": 8000,
                }
            ],
        },
    }


def _desired_hooks(path: Path, runtime: Path, install: bool) -> tuple[dict[str, Any], bool]:
    original = _read_hooks(path)
    before = json.dumps(original, sort_keys=True)
    desired = json.loads(json.dumps(original))
    _remove_managed(desired, runtime)
    if install:
        hooks = desired.setdefault("hooks", {})
        for event, group in _managed_handlers(runtime).items():
            hooks.setdefault(event, []).append(group)
    return desired, before != json.dumps(desired, sort_keys=True)


def _timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def _backup(path: Path, backup_root: Path, label: str) -> Path | None:
    if not path.exists():
        return None
    destination = backup_root / _timestamp() / label
    destination.parent.mkdir(parents=True, exist_ok=True)
    if path.is_dir():
        shutil.copytree(path, destination)
    else:
        shutil.copy2(path, destination)
    return destination


def _atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def _replace_skill(source: Path, target: Path) -> None:
    if source.resolve() == target.resolve():
        return
    temporary = target.with_name(target.name + ".tmp")
    if temporary.exists():
        shutil.rmtree(temporary)
    shutil.copytree(
        source,
        temporary,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    if target.exists():
        shutil.rmtree(target)
    temporary.replace(target)


def _write_runtime(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    shutil.copy2(source, temporary)
    os.replace(temporary, target)


def _states() -> dict[str, Any]:
    paths = targets()
    source = skill_source()
    runtime_source = source / "scripts" / "continuity_recovery.py"
    source_manifest = _file_manifest(source)
    skill_current = (
        source.resolve() == paths["skill"].resolve()
        or source_manifest == _file_manifest(paths["skill"])
    )
    runtime_current = (
        paths["runtime"].is_file()
        and _hash_bytes(paths["runtime"].read_bytes()) == _hash_bytes(runtime_source.read_bytes())
    )
    desired_hooks, hooks_change = _desired_hooks(paths["hooks"], paths["runtime"], True)
    return {
        "paths": paths,
        "source": source,
        "runtime_source": runtime_source,
        "skill_current": skill_current,
        "runtime_current": runtime_current,
        "hooks_current": not hooks_change,
        "desired_hooks": desired_hooks,
    }


def status() -> int:
    try:
        state = _states()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[error] {exc}")
        return 1
    paths = state["paths"]
    print(f"Codex home: {paths['home']}")
    print(f"Reference package: {state['source']}")
    if state["source"].resolve() == paths["skill"].resolve():
        print("[note] Installed-package self-check; synchronization with a source repository was not checked")
    print(f"Skill package: {'current' if state['skill_current'] else 'missing or drifted'}")
    print(f"Hook runtime: {'current' if state['runtime_current'] else 'missing or drifted'}")
    print(f"Hook configuration: {'current' if state['hooks_current'] else 'missing or drifted'}")
    return 0 if all(state[key] for key in ("skill_current", "runtime_current", "hooks_current")) else 1


def install(apply: bool) -> int:
    try:
        state = _states()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[error] {exc}")
        return 1
    paths = state["paths"]
    changes = [
        label
        for label, current in (
            ("synchronize skill package", state["skill_current"]),
            ("install hook runtime", state["runtime_current"]),
            ("merge PreCompact and SessionStart handlers", state["hooks_current"]),
        )
        if not current
    ]
    print(f"Codex home: {paths['home']}")
    print(f"Reference package: {state['source']}")
    if not changes:
        print("[ok] installation is current")
        return 0
    for change in changes:
        print(f"[plan] {change}")
    if not apply:
        print("[preview] no files changed; rerun with --apply")
        return 0
    try:
        if not state["skill_current"]:
            _backup(paths["skill"], paths["backups"], "skill")
            _replace_skill(state["source"], paths["skill"])
        if not state["runtime_current"]:
            _backup(paths["runtime"], paths["backups"], "continuity_recovery.py")
            _write_runtime(state["runtime_source"], paths["runtime"])
        if not state["hooks_current"]:
            _backup(paths["hooks"], paths["backups"], "hooks.json")
            _atomic_json(paths["hooks"], state["desired_hooks"])
    except OSError as exc:
        print(f"[error] install failed: {exc}")
        return 1
    print("[ok] continuity skill installed")
    return 0


def uninstall(apply: bool) -> int:
    paths = targets()
    try:
        desired_hooks, hooks_change = _desired_hooks(paths["hooks"], paths["runtime"], False)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[error] {exc}")
        return 1
    source_is_target = skill_source().resolve() == paths["skill"].resolve()
    changes: list[str] = []
    if hooks_change:
        changes.append("remove managed PreCompact and SessionStart handlers")
    if paths["runtime"].exists():
        changes.append("remove managed hook runtime")
    if paths["skill"].exists() and not source_is_target:
        changes.append("remove installed skill package")
    print(f"Codex home: {paths['home']}")
    if not changes:
        print("[ok] continuity skill is not installed")
        return 0
    for change in changes:
        print(f"[plan] {change}")
    if not apply:
        print("[preview] no files changed; rerun with --apply")
        return 0
    try:
        if hooks_change:
            _backup(paths["hooks"], paths["backups"], "hooks.json")
            _atomic_json(paths["hooks"], desired_hooks)
        if paths["runtime"].is_file():
            _backup(paths["runtime"], paths["backups"], "continuity_recovery.py")
            paths["runtime"].unlink()
        if paths["skill"].is_dir() and not source_is_target:
            _backup(paths["skill"], paths["backups"], "skill")
            shutil.rmtree(paths["skill"])
    except OSError as exc:
        print(f"[error] uninstall failed: {exc}")
        return 1
    print("[ok] continuity skill removed; recovery packets were preserved")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    for name in ("install", "uninstall"):
        command = commands.add_parser(name)
        command.add_argument("--apply", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "status":
        return status()
    if args.command == "install":
        return install(args.apply)
    if args.command == "uninstall":
        return uninstall(args.apply)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
