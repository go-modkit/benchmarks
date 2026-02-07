#!/usr/bin/env python3
import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_VERSION_FIELDS = [
    "go",
    "node",
    "npm",
    "python",
    "wrk",
    "docker",
    "docker_compose",
]


def parse_service_blocks(compose_text):
    in_services = False
    current = None
    blocks = {}
    for raw_line in compose_text.splitlines():
        line = raw_line.rstrip("\n")
        if line.strip() == "services:":
            in_services = True
            continue
        if not in_services:
            continue

        if line.startswith("  ") and line.endswith(":") and not line.startswith("    "):
            current = line.strip().rstrip(":")
            blocks[current] = []
            continue

        if current is None:
            continue

        if line.startswith("    "):
            blocks[current].append(line.strip())
            continue

        if line.strip() and not line.startswith(" "):
            break
    return blocks


def run_first_line(command):
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return "unavailable"
    output = (completed.stdout or completed.stderr or "").strip()
    if not output:
        return "unavailable"
    return output.splitlines()[0].strip()


def git_metadata():
    return {
        "commit": run_first_line(["git", "rev-parse", "HEAD"]),
        "branch": run_first_line(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
    }


def runtime_versions():
    docker_compose = run_first_line(["docker", "compose", "version", "--short"])
    if docker_compose == "unavailable":
        docker_compose = run_first_line(["docker-compose", "version", "--short"])

    return {
        "go": run_first_line(["go", "version"]),
        "node": run_first_line(["node", "--version"]),
        "npm": run_first_line(["npm", "--version"]),
        "python": run_first_line(["python3", "--version"]),
        "wrk": run_first_line(["wrk", "--version"]),
        "docker": run_first_line(["docker", "--version"]),
        "docker_compose": docker_compose,
    }


def ensure_parent(path):
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path, payload):
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def collect_fingerprint(out_path):
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "versions": runtime_versions(),
        "git": git_metadata(),
    }
    write_json(out_path, payload)
    print(f"Wrote: {out_path}")


def require_non_empty_string(data, key):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"Invalid or missing value for: {key}")


def check_fingerprint(path):
    if not path.exists():
        raise SystemExit(f"Fingerprint file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))

    versions = payload.get("versions")
    if not isinstance(versions, dict):
        raise SystemExit("Missing versions object")
    for key in REQUIRED_VERSION_FIELDS:
        require_non_empty_string(versions, key)

    git = payload.get("git")
    if not isinstance(git, dict):
        raise SystemExit("Missing git object")
    require_non_empty_string(git, "commit")
    require_non_empty_string(git, "branch")

    print("Fingerprint check passed")


def check_limits(compose_path):
    if not compose_path.exists():
        raise SystemExit(f"Compose file not found: {compose_path}")

    compose_text = compose_path.read_text(encoding="utf-8")
    service_blocks = parse_service_blocks(compose_text)
    if not service_blocks:
        raise SystemExit("No service blocks found under services:")

    missing = []
    for service, entries in service_blocks.items():
        has_cpu = any(item.startswith("cpus:") and item.split(":", 1)[1].strip() for item in entries)
        has_mem = any(item.startswith("mem_limit:") and item.split(":", 1)[1].strip() for item in entries)
        if not has_cpu or not has_mem:
            missing.append(service)

    if missing:
        raise SystemExit("Missing cpu/memory limits for services: " + ", ".join(sorted(missing)))

    print("Docker limits check passed")


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark environment metadata helpers")
    sub = parser.add_subparsers(dest="cmd", required=True)

    collect = sub.add_parser("collect-fingerprint", help="Collect runtime/toolchain fingerprint")
    collect.add_argument("--out", required=True, type=Path)

    check = sub.add_parser("check-fingerprint", help="Validate fingerprint file")
    check.add_argument("--file", required=True, type=Path)

    limits = sub.add_parser("check-limits", help="Validate docker-compose cpu/memory limits")
    limits.add_argument("--compose", required=True, type=Path)

    return parser.parse_args()


def main():
    args = parse_args()
    if args.cmd == "collect-fingerprint":
        collect_fingerprint(args.out)
        return
    if args.cmd == "check-fingerprint":
        check_fingerprint(args.file)
        return
    if args.cmd == "check-limits":
        check_limits(args.compose)
        return
    raise SystemExit(f"Unknown command: {args.cmd}")


if __name__ == "__main__":
    main()
