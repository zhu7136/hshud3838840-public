"""Training entry point for Gradmotion platform.

Usage: gm-run hshud3838840-public/run_train.py <training args...>

The Gradmotion SDK automatically installs packages from the repo before
running this script. If holosoma is still not importable, we attempt
a local pip install as fallback.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
HOLOSOMA_PATH = REPO_ROOT / "src" / "holosoma"


def ensure_holosoma():
    """Ensure holosoma is importable, installing if needed."""
    try:
        import holosoma  # noqa: F401
        print(f"[run_train.py] holosoma found: {holosoma.__file__}")
        return
    except ImportError:
        pass

    print(f"[run_train.py] holosoma not found, installing from {HOLOSOMA_PATH} ...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-e", str(HOLOSOMA_PATH)],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


if __name__ == "__main__":
    print(f"[run_train.py] Python: {sys.executable}")
    ensure_holosoma()

    from holosoma.train_agent import main
    main()
