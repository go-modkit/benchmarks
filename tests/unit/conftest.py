from __future__ import annotations

import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session", autouse=True)
def scripts_on_path(repo_root: Path) -> None:
    scripts_dir = repo_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))


@pytest.fixture()
def temp_results_dir(tmp_path: Path) -> Path:
    path = tmp_path / "results" / "latest"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def fixture_root(repo_root: Path) -> Path:
    return repo_root / "tests" / "fixtures"
