#!/bin/bash
# sim2sim_hu_d04_climb14.sh - Run sim2sim for hu_d04 on climb_14 terrain
#
# Usage:
#   Terminal 1: bash scripts/sim2sim_hu_d04_climb14.sh sim
#   Terminal 2: bash scripts/sim2sim_hu_d04_climb14.sh policy
#
# Start terminal 1 first, wait for the viewer window, then start terminal 2.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

PYTHON=/root/.holosoma_deps/miniconda3/envs/hssim/bin/python

TERRAIN_OBJ="holosoma/data/motions/g1_29dof/whole_body_tracking/terrain_climb_14_50cm.obj"
MODEL_PATH="exported/model_0133000.onnx"

run_sim() {
    cd "$PROJECT_ROOT"
    $PYTHON src/holosoma/holosoma/run_sim.py \
        simulator:mujoco \
        robot:hu-d04-29dof \
        terrain:terrain-load-obj \
        --terrain.terrain-term.obj-file-path="$TERRAIN_OBJ" \
        --robot.init-state.pos="[0.0, 0.0, 0.836]" \
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
        --task.model-path="$MODEL_PATH" \
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
