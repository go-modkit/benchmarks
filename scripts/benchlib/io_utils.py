from __future__ import annotations

import json
from pathlib import Path


def ensure_under_root(path: Path, root: Path, label: str) -> Path:
    resolved = path.resolve()
    root_resolved = root.resolve()
    if resolved == root_resolved or root_resolved in resolved.parents:
        return resolved
    raise SystemExit(f"{label} must be under {root_resolved}: {resolved}")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_json_policy(path: Path, default_on_missing=None):
    if not path.exists():
        if default_on_missing is not None:
            return default_on_missing
        raise SystemExit(f"Policy file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))
