#!/bin/sh
run_repo_python() {
  if command -v py >/dev/null 2>&1; then py -3 "$@"
  elif command -v python3 >/dev/null 2>&1; then python3 "$@"
  else python "$@"; fi
}
