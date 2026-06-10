#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Find Python - prefer IsaacSim's bundled Python, fall back to system
PYTHON=""
for p in \
    /workspace/isaaclab/_isaac_sim/kit/python/bin/python3 \
    /workspace/isaaclab/_isaac_sim/kit/python/bin/python \
    /usr/bin/python3 \
    /usr/bin/python; do
    if [ -x "$p" ]; then
        PYTHON="$p"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[run_train.sh] ERROR: No Python found"
    exit 1
fi

echo "[run_train.sh] Using Python: $PYTHON"

# Install holosoma if not already installed
if ! "$PYTHON" -c "import holosoma" 2>/dev/null; then
    echo "[run_train.sh] Installing holosoma..."
    "$PYTHON" -m pip install -e "${SCRIPT_DIR}/src/holosoma"
fi

# Forward all arguments to train_agent.py
exec "$PYTHON" "${SCRIPT_DIR}/src/holosoma/holosoma/train_agent.py" "$@"
