from __future__ import annotations

import io
import json
import shutil
from contextlib import redirect_stdout

from .script_loader import load_script_module


def test_load_raw_files_skips_malformed_json(repo_root, fixture_root, tmp_path):
    mod = load_script_module(repo_root, "scripts/generate-report.py", "generate_report_skip")

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    shutil.copy(fixture_root / "raw" / "modkit-ok.json", raw_dir / "modkit-ok.json")
    shutil.copy(fixture_root / "raw" / "modkit-invalid-json.json", raw_dir / "modkit-invalid-json.json")

    mod.RAW_DIR = raw_dir
    buf = io.StringIO()
    with redirect_stdout(buf):
        rows = mod.load_raw_files()

    assert len(rows) == 1
    assert rows[0]["framework"] == "modkit"
    assert "Warning: skipping malformed JSON" in buf.getvalue()


def test_build_summary_counts_ok_and_skipped(repo_root, fixture_root):
    mod = load_script_module(repo_root, "scripts/generate-report.py", "generate_report_summary")

    rows = [
        json.loads((fixture_root / "raw" / "modkit-ok.json").read_text(encoding="utf-8")),
        json.loads((fixture_root / "raw" / "nestjs-skipped-health.json").read_text(encoding="utf-8")),
    ]
    rows[0]["_source_file"] = "modkit-ok.json"
    rows[1]["_source_file"] = "nestjs-skipped-health.json"

    summary = mod.build_summary(rows)
    assert summary["total_targets"] == 2
    assert summary["successful_targets"] == 1
    assert summary["skipped_targets"] == 1


def test_write_report_outputs_expected_sections(repo_root, fixture_root, tmp_path):
    mod = load_script_module(repo_root, "scripts/generate-report.py", "generate_report_write")

    expected = json.loads((fixture_root / "summary" / "expected-summary.json").read_text(encoding="utf-8"))
    mod.REPORT_PATH = tmp_path / "report.md"
    mod.write_report(expected)

    content = mod.REPORT_PATH.read_text(encoding="utf-8")
    assert "## Fairness Disclaimer" in content
    assert "| modkit | ok | 600.00" in content
    assert "Parity failures invalidate performance interpretation" in content
