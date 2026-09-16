"""Run the release acceptance commands and stop on the first failure."""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


def main() -> int:
    """Verify code and the complete offline demo, optionally the container."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--docker", action="store_true", help="Also build and run the Docker image")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    python = sys.executable
    test_files = [str(path.relative_to(root)) for path in sorted((root / "tests").glob("test_se*.py"))]
    commands = [
        [python, "-m", "ruff", "check", "researcher", *test_files],
        [python, "-m", "mypy", "researcher"],
        [python, "-m", "pytest", "tests", "--cov=researcher", "--cov-report=term-missing", "--cov-fail-under=60"],
        [python, "-m", "researcher", "doctor", "--offline"],
        [python, "demo_ai.py", "--offline", "--limit", "5"],
        [python, "-m", "researcher", "demo", "--offline", "--no-cache", "--json"],
    ]
    if args.docker:
        if shutil.which("docker") is None:
            sys.stderr.write("Docker is not installed or not on PATH.\n")
            return 2
        commands += [
            ["docker", "build", "-t", "vertex-research", "."],
            ["docker", "run", "--rm", "--network", "none", "vertex-research"],
        ]
    try:
        for command in commands:
            print("Running:", " ".join(command), flush=True)
            subprocess.run(command, cwd=root, check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        sys.stderr.write(f"Verification stopped: {type(error).__name__}.\n")
        return 1
    print("Requested checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
