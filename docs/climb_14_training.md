# Climb_14 Training Guide

Training G1 robot for terrain climbing using the climb_14 motion dataset.

## Prerequisites

- Conda environment: `conda activate hssim`
- GPU with CUDA support
- IsaacSim installed

## Quick Start

```bash
# Activate environment
conda activate hssim

# Train with default z_scale=1.0 (needs 40GB+ GPU)
./scripts/train_climb_14.sh

# Train with reduced envs for 16GB GPU
./scripts/train_climb_14.sh --num_envs 512

# Train with specific z_scale
./scripts/train_climb_14.sh --z_scale 1.2 --num_envs 512

# Resume from checkpoint
./scripts/train_climb_14.sh --resume

# Check training status
./scripts/train_climb_14.sh --status
```

## Parameters

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `--z_scale` | 0.8, 0.9, 1.0, 1.1, 1.2 | 1.0 | Terrain height scale factor |
| `--num_envs` | 128-4096 | 4096 | Number of parallel environments |
| `--resume` | - | - | Resume from latest checkpoint |
| `--status` | - | - | Show training status |

### GPU Memory Requirements

| GPU VRAM | Recommended `--num_envs` |
|----------|-------------------------|
| 8 GB | 256 |
| 16 GB | 512-1024 |
| 24 GB | 1024-2048 |
| 40+ GB | 4096 |

## Data

### Pre-converted Data

Located at `src/holosoma/holosoma/data/motions/g1_29dof/whole_body_tracking/`:

- `climb_14_mj_fps50.npz` - MuJoCo-converted motion (50fps)
- `climb_14_holosoma.npz` - Simple conversion (no FK)
- `climb_14_assets/` - Terrain URDF and meshes

### Converting Other z_scale Variants

If you need a different z_scale that's not pre-converted:

```bash
# Activate environment
conda activate hssim

# Convert using MuJoCo FK (recommended)
python src/holosoma_retargeting/holosoma_retargeting/data_conversion/convert_data_format_mj.py \
  --config.input_file="OmniRetarget_Dataset/robot-terrain/climb_14_z_scale_1.2.npz" \
  --config.use_omniretarget_data=True \
  --config.output_fps=50

# Or simple conversion (no FK)
python OmniRetarget_Dataset/convert_to_holosoma.py \
  OmniRetarget_Dataset/robot-terrain/climb_14_z_scale_1.2.npz
```

## Training Configuration

The script uses the `g1-29dof-wbt-fast-sac-climb` experiment preset with:

- Algorithm: FastSAC (Soft Actor-Critic with distributional critics)
- Simulator: IsaacSim
- Robot: Unitree G1 (29 DOF)
- Motion tracking: 14 body parts

### Manual Training Command

If you need more control:

```bash
python src/holosoma/holosoma/train_agent.py \
  exp:g1-29dof-wbt-fast-sac-climb \
  --command.setup_terms.motion_command.params.motion_config.motion_file="holosoma/data/motions/g1_29dof/whole_body_tracking/climb_14_mj_fps50.npz" \
  --robot.object.object_urdf_path="holosoma/data/motions/g1_29dof/whole_body_tracking/climb_14_assets/multi_boxes_z_scale_1.0.urdf"
```

## Checkpoints

Checkpoints are saved to `logs/WholeBodyTracking/<timestamp>-g1_29dof_wbt_fast_sac_manager-locomotion/`.

Each checkpoint contains:
- `model_<step>.pt` - PyTorch model
- `model_<step>.onnx` - ONNX export for inference
- `holosoma_config.yaml` - Training configuration

## Monitoring

### WandB

Training logs are automatically uploaded to WandB if configured. Check the run ID:

```bash
cat logs/WholeBodyTracking/<latest-run>/wandb/run-id.txt
```

### TensorBoard

```bash
tensorboard --logdir logs/WholeBodyTracking/
```

## Troubleshooting

### "CUDA out of memory"

Reduce the number of parallel environments:
```bash
# For 16GB GPU
./scripts/train_climb_14.sh --num_envs 512

# For 8GB GPU
./scripts/train_climb_14.sh --num_envs 256
```

Or set PyTorch memory optimization:
```bash
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
```

### "hssim conda environment not activated"

```bash
conda activate hssim
```

### "CUDA GPU not available"

Check GPU drivers:
```bash
nvidia-smi
```

### "IsaacSim not available"

Reinstall IsaacSim in hssim environment:
```bash
bash scripts/setup_isaacsim.sh
```

### "Motion file not found"

Convert the motion data first (see Data section above).

### "Terrain URDF not found"

For z_scale != 1.0, generate the URDF or use z_scale=1.0 (pre-converted).
