"""Training entry point for Gradmotion platform.

Usage: gm-run hshud3838840-public/run_train.py <training args...>
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
HOLOSOMA_SRC = REPO_ROOT / "src" / "holosoma"


def ensure_holosoma():
    """Install holosoma and all its dependencies."""
    print(f"[run_train.py] Installing holosoma from {HOLOSOMA_SRC} ...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", str(HOLOSOMA_SRC)],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


if __name__ == "__main__":
    print(f"[run_train.py] Python: {sys.executable}")
    ensure_holosoma()

    from holosoma.train_agent import main
    main()
