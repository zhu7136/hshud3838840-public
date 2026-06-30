#!/bin/bash
# sim2sim_hu_d04.sh - Run sim2sim evaluation for hu_d04 robot
#
# Usage:
#   Terminal 1: bash scripts/sim2sim_hu_d04.sh sim
#   Terminal 2: bash scripts/sim2sim_hu_d04.sh policy
#
# Start terminal 1 first, wait for the viewer window, then start terminal 2.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

PYTHON=/root/.holosoma_deps/miniconda3/envs/hssim/bin/python

SAFETY_MODEL_PATH="logs/hv-hu-d04-manager/20260611_140050-hu_d04_29dof_fast_sac_manager-locomotion/exported/model_0010000.onnx"
WBT_MODEL_PATH="logs/WholeBodyTracking/20260610_172542-hu_d04_29dof_wbt_fast_sac_manager-locomotion/exported/model_0359000_29dof.onnx"

run_sim() {
    cd "$PROJECT_ROOT"
    $PYTHON src/holosoma/holosoma/run_sim.py \
        simulator:mujoco \
        robot:hu-d04-29dof \
        terrain:terrain-locomotion-plane \
        --robot.init-state.pos="[0.0, 0.0, 0.877]" \
        --robot.init-state.rot="[0.0, 0.0, 0.0, 1.0]" \
        --simulator.config.bridge.interface=lo \
        --simulator.config.bridge.use-joystick=False \
        --simulator.config.sim.fps=200 \
        --simulator.config.virtual-gantry.enabled=False
}

run_policy() {
    cd "$PROJECT_ROOT"
    $PYTHON src/holosoma_inference/holosoma_inference/run_policy.py \
        inference:hu-d04-29dof-wbt \
        --task.model-path="$WBT_MODEL_PATH" \
        --secondary.task.model-path="$SAFETY_MODEL_PATH" \
        --task.no-use-joystick \
        --task.use-sim-time \
        --task.rl-rate 50 \
        --task.interface lo \
        --auto-start
}

case "${1:-}" in
    sim)
        run_sim
        ;;
    policy)
        run_policy
        ;;
    *)
        echo "Usage: $0 {sim|policy}"
        echo ""
        echo "  sim     - Run MuJoCo simulator (terminal 1)"
        echo "  policy  - Run ONNX policy inference (terminal 2)"
        echo ""
        echo "Start 'sim' first, wait for viewer, then start 'policy'."
        exit 1
        ;;
esac
