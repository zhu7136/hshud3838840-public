"""Training entry point for Gradmotion platform.

Usage: gm-run hshud3838840-public/run_train.py <training args...>
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
HOLOSOMA_SRC = REPO_ROOT / "src" / "holosoma"


def fix_isaacsim_torch_vendored_packaging():
    """Fix IsaacSim's torch vendored packaging missing _structures.py."""
    import types
    
    # Create the _structures module with required classes
    class InfinityType:
        """Infinity type for packaging version."""
        def __repr__(self):
            return "Infinity"
        def __hash__(self):
            return hash("Infinity")
        def __lt__(self, other):
            return False
        def __le__(self, other):
            return isinstance(other, InfinityType)
        def __gt__(self, other):
            return not isinstance(other, InfinityType)
        def __ge__(self, other):
            return True
        def __eq__(self, other):
            return isinstance(other, InfinityType)
        def __ne__(self, other):
            return not isinstance(other, InfinityType)
    
    class NegativeInfinityType:
        """Negative infinity type for packaging version."""
        def __repr__(self):
            return "-Infinity"
        def __hash__(self):
            return hash("-Infinity")
        def __lt__(self, other):
            return True
        def __le__(self, other):
            return True
        def __gt__(self, other):
            return False
        def __ge__(self, other):
            return not isinstance(other, NegativeInfinityType)
        def __eq__(self, other):
            return isinstance(other, NegativeInfinityType)
        def __ne__(self, other):
            return not isinstance(other, NegativeInfinityType)
    
    # Create the module
    structures_module = types.ModuleType("torch._vendor.packaging._structures")
    structures_module.InfinityType = InfinityType
    structures_module.NegativeInfinityType = NegativeInfinityType
    structures_module.Infinity = InfinityType()
    structures_module.NegativeInfinity = NegativeInfinityType()
    
    # Register the module in sys.modules
    import sys
    sys.modules["torch._vendor.packaging._structures"] = structures_module
    print("[run_train.py] Injected torch._vendor.packaging._structures module")


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
    # packaging<24 is now specified in pyproject.toml dependencies


if __name__ == "__main__":
    print(f"[run_train.py] Python: {sys.executable}")
    
    # Disable torch inductor to avoid compilation issues
    os.environ["TORCH_COMPILE_DISABLE"] = "1"
    os.environ["TORCHDYNAMO_DISABLE"] = "1"
    print("[run_train.py] Disabled torch inductor compilation")
    
    ensure_holosoma()
    
    # Fix IsaacSim torch vendored packaging before importing torch
    fix_isaacsim_torch_vendored_packaging()

    from holosoma.train_agent import main
    main()
