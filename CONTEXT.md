# Holosoma Project Context

## Overview

Holosoma is a robot simulation and training framework for Unitree robots, built on IsaacSim.

## Architecture

- **Core**: `src/holosoma/` - Main package
- **Simulator**: `src/holosoma/holosoma/simulator/isaacsim/` - IsaacSim integration
- **Config**: `src/holosoma/holosoma/config_values/` - Robot and training configurations
- **Data**: `src/holosoma/holosoma/data/` - Robots, motions, and terrain assets
- **Managers**: `src/holosoma/holosoma/managers/` - Training managers (rewards, terminations, etc.)

## Key Concepts

- **Whole Body Tracking (WBT)**: Motion tracking for humanoid robots
- **FastSAC**: Distributional Soft Actor-Critic algorithm
- **Terrain**: Custom terrain loading from OBJ files

## Development

- Use `gm-run` for training execution on Gradmotion platform
- Checkpoint logs saved to `logs/WholeBodyTracking/`
- Training configs in `src/holosoma/holosoma/config_values/wbt/`

## Conventions

- Follow PEP 8 for Python code
- Use dataclasses for configuration
- Keep configs in dedicated files under `config_values/`
