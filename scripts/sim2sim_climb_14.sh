#!/bin/bash
# sim2sim_climb_14.sh - Run sim2sim evaluation for climb_14 terrain
#
# Usage:
#   Terminal 1: bash scripts/sim2sim_climb_14.sh sim
#   Terminal 2: bash scripts/sim2sim_climb_14.sh policy
#
# Start terminal 1 first, wait for the viewer window, then start terminal 2.

set -e

source /root/.holosoma_deps/miniconda3/bin/activate hssim

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

MOTION_FILE="holosoma/data/motions/g1_29dof/whole_body_tracking/climb_14_mj_fps50_no_obj.npz"
TERRAIN_OBJ="holosoma/data/motions/g1_29dof/whole_body_tracking/terrain_climb_14_50cm.obj"
MODEL_PATH="logs/WholeBodyTracking/20260604_161649-g1_29dof_wbt_fast_sac_manager-locomotion/exported/model_0400000.onnx"

run_sim() {
    cd "$PROJECT_ROOT"
    python src/holosoma/holosoma/run_sim.py \
        simulator:mujoco \
        robot:g1-29dof \
        terrain:terrain-load-obj \
        --terrain.terrain-term.obj-file-path="$TERRAIN_OBJ" \
        --robot.init-state.pos="[0.0, -1.5, 0.96]" \
        --robot.init-state.rot="[0.0, 0.0, 0.7071, 0.7071]" \
        --simulator.config.bridge.interface=lo \
        --simulator.config.bridge.use-joystick=False \
        --simulator.config.sim.fps=200
}

run_policy() {
    cd "$PROJECT_ROOT"
    python3 src/holosoma_inference/holosoma_inference/run_policy.py \
        inference:g1-29dof-wbt \
        --task.model-path="$MODEL_PATH" \
        --task.no-use-joystick \
        --task.use-sim-time \
        --task.rl-rate 50 \
        --task.interface lo
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
