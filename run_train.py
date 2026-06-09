#!/usr/bin/env python3
"""Training entry point that ensures holosoma is installed before running."""

import subprocess
import sys
from pathlib import Path


def ensure_holosoma_installed():
    """Install holosoma in editable mode if not already installed."""
    try:
        import holosoma  # noqa: F401
    except ImportError:
        # Find the holosoma package relative to this script
        repo_root = Path(__file__).resolve().parent
        holosoma_path = repo_root / "src" / "holosoma"
        if not holosoma_path.exists():
            print(f"ERROR: holosoma package not found at {holosoma_path}")
            sys.exit(1)
        print(f"Installing holosoma from {holosoma_path} ...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-e", str(holosoma_path)],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )


if __name__ == "__main__":
    ensure_holosoma_installed()

    # Forward all CLI args to train_agent.py
    from holosoma.train_agent import main

    main()
