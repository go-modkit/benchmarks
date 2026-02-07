#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - exercised in environments without dependency
    Draft202012Validator = None


ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "results" / "latest" / "raw"
RAW_SCHEMA = ROOT / "schemas" / "benchmark-raw-v1.schema.json"
SUMMARY_FILE = ROOT / "results" / "latest" / "summary.json"
SUMMARY_SCHEMA = ROOT / "schemas" / "benchmark-summary-v1.schema.json"


def load_json(path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise SystemExit(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Malformed JSON in {path}: {exc.msg} at line {exc.lineno}, column {exc.colno}") from exc


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


def validate_jsonschema(payload, schema, path, artifact_label):
    if Draft202012Validator is None:
        raise SystemExit(
            "jsonschema dependency is required for schema validation. Install with: python3 -m pip install jsonschema"
        )

    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(payload),
        key=lambda err: [str(part) for part in err.path],
    )
    if not errors:
        return
    first = errors[0]
    path_suffix = ".".join(str(part) for part in first.path)
    field = f" ({path_suffix})" if path_suffix else ""
    raise SystemExit(f"{artifact_label} JSON Schema validation failed for {path}{field}: {first.message}")


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
        validate_jsonschema(payload, schema, path, "Raw")
        validate_raw_row(path, payload, schema_version)

    print(f"benchmark-raw-schema-check: validated {len(files)} raw artifact(s)")


def validate_summary(summary_file, schema_path):
    schema = load_json(schema_path)
    schema_version = (schema.get("properties") or {}).get("schema_version", {}).get("const")
    if not isinstance(schema_version, str) or not schema_version:
        raise SystemExit(f"Summary schema file missing properties.schema_version.const: {schema_path}")

    if not summary_file.exists():
        raise SystemExit(f"Summary file not found: {summary_file}")

    payload = load_json(summary_file)
    validate_jsonschema(payload, schema, summary_file, "Summary")
    required = (
        "schema_version",
        "generated_at",
        "total_targets",
        "successful_targets",
        "skipped_targets",
        "targets",
    )
    for field in required:
        if field not in payload:
            raise SystemExit(f"Summary schema validation failed for {summary_file}: missing {field}")

    if payload.get("schema_version") != schema_version:
        raise SystemExit(
            f"Summary schema validation failed for {summary_file}: schema_version={payload.get('schema_version')!r}, expected {schema_version!r}"
        )

    targets = payload.get("targets")
    if not isinstance(targets, list):
        raise SystemExit(f"Summary schema validation failed for {summary_file}: targets must be array")

    for idx, target in enumerate(targets):
        if not isinstance(target, dict):
            raise SystemExit(f"Summary schema validation failed for {summary_file}: targets[{idx}] must be object")
        for field in ("framework", "status", "target", "provenance"):
            if field not in target:
                raise SystemExit(f"Summary schema validation failed for {summary_file}: targets[{idx}] missing {field}")
        provenance = target.get("provenance")
        if not isinstance(provenance, dict) or not provenance.get("raw_source"):
            raise SystemExit(
                f"Summary schema validation failed for {summary_file}: targets[{idx}].provenance.raw_source is required"
            )

        status = target.get("status")
        if status == "ok" and "uncertainty" not in target:
            raise SystemExit(
                f"Summary schema validation failed for {summary_file}: targets[{idx}] missing uncertainty for status=ok"
            )

    print("benchmark-summary-schema-check: validated summary artifact")


def parse_args():
    parser = argparse.ArgumentParser(description="Validate benchmark result schemas")
    parser.add_argument("cmd", choices=["raw-check", "summary-check"])
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--raw-schema", type=Path, default=RAW_SCHEMA)
    parser.add_argument("--summary-file", type=Path, default=SUMMARY_FILE)
    parser.add_argument("--summary-schema", type=Path, default=SUMMARY_SCHEMA)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.cmd == "raw-check":
        validate_raw(args.raw_dir, args.raw_schema)
        return
    if args.cmd == "summary-check":
        validate_summary(args.summary_file, args.summary_schema)
        return
    raise SystemExit(f"Unknown command: {args.cmd}")


if __name__ == "__main__":
    main()
