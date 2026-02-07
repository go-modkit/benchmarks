from __future__ import annotations

import shutil

import pytest

from .script_loader import load_script_module


def test_validate_raw_accepts_ok_and_skipped(repo_root, fixture_root, tmp_path):
    mod = load_script_module(repo_root, "scripts/validate-result-schemas.py", "validate_result_schemas")

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    shutil.copy(fixture_root / "raw" / "modkit-ok.json", raw_dir / "modkit-ok.json")
    shutil.copy(fixture_root / "raw" / "nestjs-skipped-health.json", raw_dir / "nestjs-skipped-health.json")

    mod.validate_raw(raw_dir, repo_root / "schemas" / "benchmark-raw-v1.schema.json")


def test_validate_raw_rejects_missing_required_fields(repo_root, fixture_root, tmp_path):
    mod = load_script_module(repo_root, "scripts/validate-result-schemas.py", "validate_result_schemas_missing")

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    shutil.copy(
        fixture_root / "raw" / "modkit-missing-required.json",
        raw_dir / "modkit-missing-required.json",
    )

    with pytest.raises(SystemExit, match="required property"):
        mod.validate_raw(raw_dir, repo_root / "schemas" / "benchmark-raw-v1.schema.json")


def test_load_json_rejects_malformed_json(repo_root, fixture_root):
    mod = load_script_module(repo_root, "scripts/validate-result-schemas.py", "validate_result_schemas_invalid")

    with pytest.raises(SystemExit, match="Malformed JSON"):
        mod.load_json(fixture_root / "raw" / "modkit-invalid-json.json")


def test_validate_summary_rejects_ok_target_without_uncertainty(repo_root, tmp_path):
    mod = load_script_module(repo_root, "scripts/validate-result-schemas.py", "validate_result_schemas_summary")

    summary = tmp_path / "summary.json"
    summary.write_text(
        """
{
  "schema_version": "summary-v1",
  "generated_at": "2026-01-01T00:00:00+00:00",
  "total_targets": 1,
  "successful_targets": 1,
  "skipped_targets": 0,
  "targets": [
    {
      "framework": "modkit",
      "status": "ok",
      "target": "http://localhost:3001",
      "provenance": {"raw_source": "results/latest/raw/modkit-ok.json"}
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="required property"):
        mod.validate_summary(summary, repo_root / "schemas" / "benchmark-summary-v1.schema.json")
