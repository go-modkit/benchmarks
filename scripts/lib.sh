#!/usr/bin/env bash

resolve_path() {
  python3 - <<'PY' "$1"
from pathlib import Path
import sys
print(Path(sys.argv[1]).resolve())
PY
}

ensure_path_under_root() {
  local var_name="$1"
  local path_value="$2"
  local root_value="$3"
  case "$path_value" in
    "$root_value"|"$root_value"/*) ;;
    *)
      echo "$var_name must be under $root_value (got: $path_value)" >&2
      return 1
      ;;
  esac
}
