from __future__ import annotations

import pytest

from .script_loader import load_script_module


def test_parse_service_blocks_extracts_services(repo_root):
    mod = load_script_module(repo_root, "scripts/environment-manifest.py", "environment_manifest_blocks")

    text = """
services:
  app:
    image: example
    cpus: \"1\"
    mem_limit: 512m
  db:
    image: postgres
    cpus: \"1\"
    mem_limit: 512m
""".strip()
    blocks = mod.parse_service_blocks(text)
    assert set(blocks.keys()) == {"app", "db"}


def test_ensure_under_results_rejects_external_path(repo_root, tmp_path):
    mod = load_script_module(repo_root, "scripts/environment-manifest.py", "environment_manifest_paths")

    with pytest.raises(SystemExit, match="Refusing path outside results/latest"):
        mod.ensure_under_results(tmp_path / "bad.json")
