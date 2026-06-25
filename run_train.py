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
    # Find IsaacSim's torch __init__.py to locate the vendored packaging
    torch_init = None
    for p in Path("/workspace/isaaclab/_isaac_sim").rglob("torch/__init__.py"):
        if "pip_prebundle" in str(p) or "_vendor" in str(p.parent):
            torch_init = p
            break
    
    if torch_init is None:
        print("[run_train.py] IsaacSim torch not found, skipping fix")
        return
    
    torch_dir = torch_init.parent
    vendor_packaging = torch_dir / "_vendor" / "packaging"
    
    # Create the _vendor/packaging directory structure if it doesn't exist
    vendor_packaging.mkdir(parents=True, exist_ok=True)
    
    structures_file = vendor_packaging / "_structures.py"
    if structures_file.exists():
        print(f"[run_train.py] _structures.py already exists at {structures_file}")
        return
    
    # Find system packaging's _structures.py
    import packaging
    packaging_dir = Path(packaging.__file__).parent
    source_structures = packaging_dir / "_structures.py"
    
    if not source_structures.exists():
        print(f"[run_train.py] Warning: source _structures.py not found at {source_structures}")
        return
    
    print(f"[run_train.py] Fixing IsaacSim torch vendored packaging: copying _structures.py to {vendor_packaging}")
    shutil.copy2(source_structures, structures_file)
    print(f"[run_train.py] Copied _structures.py to {structures_file}")


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
    ensure_holosoma()
    
    # Fix IsaacSim torch vendored packaging before importing torch
    fix_isaacsim_torch_vendored_packaging()

    from holosoma.train_agent import main
    main()
