#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "results" / "latest" / "raw"
RAW_SCHEMA = ROOT / "schemas" / "benchmark-raw-v1.schema.json"


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_raw_row(path, payload, schema_version):
    required = ("schema_version", "framework", "target", "status")
    for field in required:
        if field not in payload:
            raise SystemExit(f"Raw schema validation failed for {path}: missing {field}")

    if payload.get("schema_version") != schema_version:
        raise SystemExit(
            f"Raw schema validation failed for {path}: schema_version={payload.get('schema_version')!r}, expected {schema_version!r}"
        )

    status = payload.get("status")
    if status not in ("ok", "skipped"):
        raise SystemExit(f"Raw schema validation failed for {path}: status={status!r} must be 'ok' or 'skipped'")

    if not isinstance(payload.get("framework"), str) or not payload.get("framework"):
        raise SystemExit(f"Raw schema validation failed for {path}: framework must be non-empty string")
    if not isinstance(payload.get("target"), str) or not payload.get("target"):
        raise SystemExit(f"Raw schema validation failed for {path}: target must be non-empty string")

    if status == "skipped":
        reason = payload.get("reason")
        if not isinstance(reason, str) or not reason:
            raise SystemExit(f"Raw schema validation failed for {path}: skipped rows require non-empty reason")
        return

    for field in ("parity", "engine", "metric_units", "benchmark", "resources_normalized"):
        if field not in payload:
            raise SystemExit(f"Raw schema validation failed for {path}: missing {field}")

    benchmark = payload.get("benchmark")
    if not isinstance(benchmark, dict):
        raise SystemExit(f"Raw schema validation failed for {path}: benchmark must be object")

    for metric_field in ("run_stats", "median"):
        if metric_field not in benchmark:
            raise SystemExit(f"Raw schema validation failed for {path}: benchmark.{metric_field} is required")


def validate_raw(raw_dir, schema_path):
    schema = load_json(schema_path)
    schema_version = (schema.get("properties") or {}).get("schema_version", {}).get("const")
    if not isinstance(schema_version, str) or not schema_version:
        raise SystemExit(f"Raw schema file missing properties.schema_version.const: {schema_path}")

    files = sorted(raw_dir.glob("*.json"))
    if not files:
        raise SystemExit(f"No raw benchmark files found in: {raw_dir}")

    for path in files:
        payload = load_json(path)
        validate_raw_row(path, payload, schema_version)

    print(f"benchmark-raw-schema-check: validated {len(files)} raw artifact(s)")


def parse_args():
    parser = argparse.ArgumentParser(description="Validate benchmark result schemas")
    parser.add_argument("cmd", choices=["raw-check"])
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--raw-schema", type=Path, default=RAW_SCHEMA)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.cmd == "raw-check":
        validate_raw(args.raw_dir, args.raw_schema)
        return
    raise SystemExit(f"Unknown command: {args.cmd}")


if __name__ == "__main__":
    main()
