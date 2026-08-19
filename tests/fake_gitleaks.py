from __future__ import annotations

import os
import sys
from pathlib import Path


capture = os.environ.get("FAKE_GITLEAKS_CAPTURE")
if capture:
    Path(capture).write_text("\n".join(sys.argv[1:]) + "\n", encoding="utf-8")

output = os.environ.get("FAKE_GITLEAKS_OUTPUT")
if output:
    print(output)

raise SystemExit(int(os.environ.get("FAKE_GITLEAKS_EXIT", "0")))
