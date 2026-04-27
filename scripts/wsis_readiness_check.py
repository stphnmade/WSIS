#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(label: str, command: list[str]) -> None:
    print(f"\n== {label} ==")
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    python = sys.executable
    run_step("Compile Python", [python, "-m", "compileall", "src", "apps", "tests", "scripts"])
    run_step("Rebuild canonical city profiles", [python, "scripts/rebuild_city_profiles.py"])
    run_step("Run tests", [python, "-m", "pytest", "-q"])
    run_step("Check diff whitespace", ["git", "diff", "--check"])
    print("\nWSIS readiness checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
