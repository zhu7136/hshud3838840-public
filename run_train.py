"""Training entry point for Gradmotion platform.

Usage: gm-run hshud3838840-public/run_train.py <training args...>
"""

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
HOLOSOMA_SRC = REPO_ROOT / "src" / "holosoma"


def ensure_holosoma():
    """Install holosoma and all its dependencies."""
    print(f"[run_train.py] Installing holosoma from {HOLOSOMA_SRC} ...")
    cmd = [sys.executable, "-m", "pip", "install", str(HOLOSOMA_SRC)]
    pip_mirror = "https://pypi.tuna.tsinghua.edu.cn/simple"
    cmd.extend(["-i", pip_mirror])
    subprocess.check_call(
        cmd,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    # Pin packaging<24 for IsaacSim torch compatibility
    # Use --force-reinstall to override pip's dependency resolver conflicts
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "packaging<24", "--force-reinstall", "-i", pip_mirror],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


if __name__ == "__main__":
    print(f"[run_train.py] Python: {sys.executable}")
    ensure_holosoma()

    from holosoma.train_agent import main
    main()
