"""Training entry point for Gradmotion platform.

Usage: gm-run hshud3838840-public/run_train.py <training args...>
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
HOLOSOMA_SRC = REPO_ROOT / "src" / "holosoma"


def ensure_holosoma():
    """Ensure holosoma is importable."""
    # 1. Try import directly
    try:
        import holosoma  # noqa: F401
        print(f"[run_train.py] holosoma found: {holosoma.__file__}")
        return
    except ImportError:
        pass

    # 2. Try adding source dir to sys.path (fastest, no install needed)
    src_str = str(HOLOSOMA_SRC)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)
    try:
        import holosoma  # noqa: F401
        print(f"[run_train.py] holosoma found via sys.path: {holosoma.__file__}")
        return
    except ImportError:
        pass

    # 3. Fallback: pip install
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
