from __future__ import annotations

import importlib.util
from pathlib import Path


def load_script_module(repo_root: Path, relative_path: str, module_name: str):
    path = repo_root / relative_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
