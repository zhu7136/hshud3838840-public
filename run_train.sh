#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Install holosoma if not already installed
if ! python -c "import holosoma" 2>/dev/null; then
    echo "[run_train.sh] Installing holosoma..."
    pip install -e "${SCRIPT_DIR}/src/holosoma"
fi

# Forward all arguments to train_agent.py
exec python "${SCRIPT_DIR}/src/holosoma/holosoma/train_agent.py" "$@"
