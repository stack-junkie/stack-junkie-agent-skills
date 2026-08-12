from __future__ import annotations

import os
import sys
from pathlib import Path


capture = os.environ.get("FAKE_GITLEAKS_CAPTURE")
if capture:
    Path(capture).write_text("\n".join(sys.argv[1:]) + "\n", encoding="utf-8")

capture_tree = os.environ.get("FAKE_GITLEAKS_CAPTURE_TREE")
if capture_tree and sys.argv:
    scan_root = Path(sys.argv[-1])
    rows = []
    if scan_root.is_dir():
        for path in sorted(item for item in scan_root.rglob("*") if item.is_file()):
            relative = path.relative_to(scan_root).as_posix()
            content = path.read_bytes().decode("utf-8", errors="replace")
            rows.append(f"{relative}={content}")
    Path(capture_tree).write_text("\n".join(rows), encoding="utf-8")

output = os.environ.get("FAKE_GITLEAKS_OUTPUT")
if output:
    print(output)

raise SystemExit(int(os.environ.get("FAKE_GITLEAKS_EXIT", "0")))
