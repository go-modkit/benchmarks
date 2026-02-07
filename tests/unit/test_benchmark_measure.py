from __future__ import annotations

from .script_loader import load_script_module


def test_parse_mem_to_mb_and_cpu_percent(repo_root):
    mod = load_script_module(repo_root, "scripts/benchmark-measure.py", "benchmark_measure_parse")

    assert mod.parse_mem_to_mb("128MiB / 1GiB") == 128.0
    assert mod.parse_mem_to_mb("1GiB / 2GiB") == 1024.0
    assert mod.parse_cpu_percent("12.5%") == 12.5


def test_coefficient_of_variation_and_iqr(repo_root):
    mod = load_script_module(repo_root, "scripts/benchmark-measure.py", "benchmark_measure_stats")

    cv = mod.coefficient_of_variation([100.0, 100.0, 100.0])
    assert cv == 0.0

    outlier_indexes, lower, upper = mod.detect_iqr_outlier_indexes([100.0, 101.0, 99.0, 500.0])
    assert outlier_indexes == {3}
    assert lower is not None
    assert upper is not None
