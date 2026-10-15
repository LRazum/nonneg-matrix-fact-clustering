#!/usr/bin/env python3
"""Keep Claude's Stop hook on the same checks as Codex and the local CLI."""
import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    script = Path(__file__).resolve().parents[2] / "tools/check_before_stop.py"
    sys.argv = [str(script), "--hook"]
    runpy.run_path(str(script), run_name="__main__")
