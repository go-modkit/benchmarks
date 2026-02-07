from __future__ import annotations

import pytest

from .script_loader import load_script_module


def test_parse_delta_percent(repo_root):
    mod = load_script_module(repo_root, "scripts/benchmark-quality-check.py", "benchmark_quality_delta")

    output = "name old new delta\nBenchmarkbaseline-8 100 115 +15.0%\n"
    assert mod.parse_delta_percent(output) == 15.0
    assert mod.parse_delta_percent("no percent here") is None


def test_ensure_under_results_rejects_outside_path(repo_root, tmp_path):
    mod = load_script_module(repo_root, "scripts/benchmark-quality-check.py", "benchmark_quality_paths")

    with pytest.raises(SystemExit, match="must be under"):
        mod.ensure_under_results(tmp_path / "outside.json", "Summary file")
