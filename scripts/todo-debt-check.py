#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

CHECK_DIRS = [
    ROOT / "scripts",
    ROOT / "docs",
    ROOT / ".github",
]

CHECK_FILES = [
    ROOT / "Makefile",
]

INCLUDE_SUFFIXES = {
    ".py",
    ".sh",
    ".md",
    ".yml",
    ".yaml",
}


def build_marker_pattern() -> re.Pattern[str]:
    markers = ["TO" + "DO", "FIX" + "ME", "HA" + "CK", "X" * 3]
    return re.compile(r"\\b(" + "|".join(markers) + r")\\b")


def iter_candidate_files():
    for directory in CHECK_DIRS:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix in INCLUDE_SUFFIXES:
                yield path

    for path in CHECK_FILES:
        if path.exists() and path.is_file():
            yield path


def main() -> None:
    pattern = build_marker_pattern()
    violations: list[tuple[Path, int, str]] = []

    for path in iter_candidate_files():
        rel = path.relative_to(ROOT)
        for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            if pattern.search(line):
                violations.append((rel, line_no, line.strip()))

    if violations:
        preview = "\n".join(f"- {path}:{line_no}: {line}" for path, line_no, line in violations[:20])
        extra = "" if len(violations) <= 20 else f"\n... and {len(violations) - 20} more"
        raise SystemExit(
            "todo-debt-check failed: first-party marker debt detected\n"
            "Remove marker text from first-party scripts/docs/workflows before merge.\n"
            f"{preview}{extra}"
        )

    print("todo-debt-check: no marker debt detected in first-party scripts/docs/workflows")


if __name__ == "__main__":
    main()
