#!/usr/bin/env python3
"""Check the existing locked project environment, syntax and tests."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    try:
        status = subprocess.run(
            ["uv", "--no-cache", "sync", "--locked", "--check"], cwd=ROOT, check=False,
        ).returncode
    except FileNotFoundError:
        print("Project checks require uv. Install uv and run uv sync --locked.", file=sys.stderr)
        return 1
    if status != 0:
        print("Project environment check failed. Set it up with uv sync --locked.", file=sys.stderr)
        return status

    commands = [
        ["python", "-m", "compileall", "-q", "src", "tests"],
        ["python", "-m", "unittest", "discover", "-s", "tests", "-v"],
    ]
    for command in commands:
        status = subprocess.run(
            ["uv", "--no-cache", "run", "--no-sync", *command], cwd=ROOT, check=False,
        ).returncode
        if status != 0:
            return status
    return 0


if __name__ == "__main__":
    sys.exit(main())
