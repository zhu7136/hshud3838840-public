#!/bin/bash
# train_climb_14.sh - One-click training for climb_14 terrain climbing motion
#
# Usage:
#   ./scripts/train_climb_14.sh                    # Default: z_scale=1.0
#   ./scripts/train_climb_14.sh --z_scale 1.2      # Specify z_scale
#   ./scripts/train_climb_14.sh --num_envs 512     # Reduce for small GPU
#   ./scripts/train_climb_14.sh --resume            # Resume from checkpoint
#   ./scripts/train_climb_14.sh --status            # Show training status

set -e

# ============================================================================
# Configuration
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

MOTION_BASE_DIR="holosoma/data/motions/g1_29dof/whole_body_tracking"
ASSETS_DIR="${MOTION_BASE_DIR}/climb_14_assets"
LOGS_DIR="${PROJECT_ROOT}/logs/WholeBodyTracking"

DEFAULT_Z_SCALE="1.0"
VALID_Z_SCALES=("0.8" "0.9" "1.0" "1.1" "1.2")

EXPERIMENT="g1-29dof-wbt-fast-sac-climb"

# ============================================================================
# Functions
# ============================================================================
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  --z_scale VALUE    Z-scale factor (0.8, 0.9, 1.0, 1.1, 1.2). Default: 1.0
  --num_envs VALUE   Number of parallel environments. Default: 4096
                     Use 512-1024 for GPUs with 16GB VRAM
  --visual           Enable visualization (disable headless mode)
  --record           Enable headless video recording
  --resume           Resume training from latest checkpoint
  --status           Show training status for latest run
  --help             Show this help message

Examples:
  $(basename "$0")                     # Train with z_scale=1.0, 4096 envs
  $(basename "$0") --z_scale 1.2       # Train with z_scale=1.2
  $(basename "$0") --num_envs 512      # Train with 512 envs (small GPU)
  $(basename "$0") --visual            # Show visualization window
  $(basename "$0") --record            # Record video in headless mode
  $(basename "$0") --resume            # Resume latest training
EOF
    exit 0
}

log_info() {
    echo "[INFO] $*"
}

log_error() {
    echo "[ERROR] $*" >&2
}

log_warn() {
    echo "[WARN] $*"
}

# Validate z_scale value
validate_z_scale() {
    local z_scale="$1"
    for valid in "${VALID_Z_SCALES[@]}"; do
        if [[ "$z_scale" == "$valid" ]]; then
            return 0
        fi
    done
    log_error "Invalid z_scale: $z_scale. Valid values: ${VALID_Z_SCALES[*]}"
    exit 1
}

# Check environment dependencies
check_environment() {
    # Check conda environment
    if [[ -z "$CONDA_DEFAULT_ENV" || "$CONDA_DEFAULT_ENV" != "hssim" ]]; then
        log_error "hssim conda environment not activated."
        log_error "Run: conda activate hssim"
        exit 1
    fi

    # Check GPU
    if ! python3 -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
        log_error "CUDA GPU not available."
        log_error "Check GPU drivers and CUDA installation."
        exit 1
    fi

    # Check IsaacSim
    if ! python3 -c "import isaacsim" 2>/dev/null; then
        log_error "IsaacSim not available."
        log_error "Ensure IsaacSim is installed in hssim environment."
        exit 1
    fi

    log_info "Environment check passed"
}

# Get motion file path for given z_scale
get_motion_file() {
    local z_scale="$1"
    echo "${MOTION_BASE_DIR}/climb_14_mj_fps50_no_obj.npz"
}

# Get terrain URDF path for given z_scale
get_terrain_urdf() {
    local z_scale="$1"
    echo "${ASSETS_DIR}/multi_boxes_z_scale_${z_scale}.urdf"
}

# Find latest climb_14 checkpoint
find_latest_checkpoint() {
    local latest_dir
    latest_dir=$(find "$LOGS_DIR" -maxdepth 1 -type d -name "*climb*" -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)

    if [[ -z "$latest_dir" ]]; then
        echo ""
        return
    fi

    # Find latest checkpoint file
    local latest_ckpt
    latest_ckpt=$(find "$latest_dir" -name "model_*.pt" -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)

    echo "$latest_ckpt"
}

# Show training status
show_status() {
    local latest_dir
    latest_dir=$(find "$LOGS_DIR" -maxdepth 1 -type d -name "*climb*" -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)

    if [[ -z "$latest_dir" ]]; then
        log_warn "No climb_14 training runs found"
        exit 0
    fi

    echo "=== Latest Climb_14 Training ==="
    echo "Directory: $latest_dir"
    echo ""

    # Find checkpoints
    local ckpt_count
    ckpt_count=$(find "$latest_dir" -name "model_*.pt" 2>/dev/null | wc -l)
    echo "Checkpoints: $ckpt_count"

    if [[ $ckpt_count -gt 0 ]]; then
        local latest_ckpt
        latest_ckpt=$(find "$latest_dir" -name "model_*.pt" -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
        echo "Latest checkpoint: $latest_ckpt"

        # Extract step number from filename
        local step
        step=$(basename "$latest_ckpt" | grep -oP '\d+' | head -1)
        echo "Training steps: $step"
    fi

    # Check for WandB run
    if [[ -f "$latest_dir/wandb/run-id.txt" ]]; then
        local run_id
        run_id=$(cat "$latest_dir/wandb/run-id.txt")
        echo "WandB run ID: $run_id"
    fi

    echo ""
    echo "Config: $latest_dir/holosoma_config.yaml"
}

# ============================================================================
# Main
# ============================================================================
main() {
    local z_scale="$DEFAULT_Z_SCALE"
    local num_envs=""
    local visual=false
    local record=false
    local resume=false
    local status=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --z_scale)
                z_scale="$2"
                shift 2
                ;;
            --num_envs)
                num_envs="$2"
                shift 2
                ;;
            --visual)
                visual=true
                shift
                ;;
            --record)
                record=true
                shift
                ;;
            --resume)
                resume=true
                shift
                ;;
            --status)
                status=true
                shift
                ;;
            --help|-h)
                usage
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                ;;
        esac
    done

    # Handle --status
    if [[ "$status" == true ]]; then
        show_status
        exit 0
    fi

    # Validate z_scale
    validate_z_scale "$z_scale"

    # Check environment
    check_environment

    # Get paths
    local motion_file
    motion_file=$(get_motion_file "$z_scale")
    local terrain_urdf
    terrain_urdf=$(get_terrain_urdf "$z_scale")

    # Verify files exist
    if [[ ! -f "$PROJECT_ROOT/src/holosoma/$motion_file" ]]; then
        log_error "Motion file not found: $motion_file"
        log_error "Run data conversion first or use z_scale=1.0 (pre-converted)"
        exit 1
    fi

    if [[ ! -f "$PROJECT_ROOT/src/holosoma/$terrain_urdf" ]]; then
        log_error "Terrain URDF not found: $terrain_urdf"
        log_error "Generate URDF for z_scale=$z_scale first"
        exit 1
    fi

    # Build training command
    local terrain_obj="holosoma/data/motions/g1_29dof/whole_body_tracking/terrain_climb_14_50cm.obj"
    local cmd=(
        python3 "$PROJECT_ROOT/src/holosoma/holosoma/train_agent.py"
        "exp:$EXPERIMENT"
        "terrain:terrain-load-obj"
        "--command.setup_terms.motion_command.params.motion_config.motion_file=$motion_file"
        "--terrain.terrain-term.obj-file-path=$terrain_obj"
        "--simulator.config.scene.env_spacing=0.0"
    )

    # Add num_envs if specified
    if [[ -n "$num_envs" ]]; then
        cmd+=("--training.num_envs=$num_envs")
    fi

    # Add visual mode if specified
    if [[ "$visual" == true ]]; then
        cmd+=("--training.headless=False")
    fi

    # Add recording if specified
    if [[ "$record" == true ]]; then
        cmd+=("--logger.headless_recording=True")
    fi

    # Handle --resume
    if [[ "$resume" == true ]]; then
        local checkpoint
        checkpoint=$(find_latest_checkpoint)
        if [[ -n "$checkpoint" ]]; then
            log_info "Resuming from checkpoint: $checkpoint"
            cmd+=("--training.checkpoint=$checkpoint")
        else
            log_warn "No checkpoint found, starting from scratch"
        fi
    fi

    # Print configuration
    echo "=========================================="
    echo "Climb_14 Training Configuration"
    echo "=========================================="
    echo "z_scale:      $z_scale"
    echo "num_envs:     ${num_envs:-4096 (default)}"
    echo "headless:     $([ "$visual" == true ] && echo "False (visualization)" || echo "True (headless)")"
    echo "recording:    $([ "$record" == true ] && echo "Enabled" || echo "Disabled")"
    echo "motion_file:  $motion_file"
    echo "terrain_obj:  $terrain_obj"
    echo "experiment:   $EXPERIMENT"
    echo "=========================================="
    echo ""

    # Execute training
    log_info "Starting training..."
    cd "$PROJECT_ROOT"
    "${cmd[@]}"
}

main "$@"
