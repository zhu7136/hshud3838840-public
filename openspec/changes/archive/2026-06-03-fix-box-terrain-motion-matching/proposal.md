## Why

当前 climb_14 训练配置中，box 障碍物作为单独的 RigidObject 或 Articulation 加载时无法正确固定在地面，导致 box 乱飞。同时，地形文件 `terrain_climb_14_with_boxes.obj` 中的 box 高度（0.38 米）与实际 box 模型高度（0.64 米）不匹配，导致动作文件无法正确配合。

## What Changes

- 将 box 作为地形加载，而不是单独的对象
- 生成正确的地形文件，确保 box 高度与实际模型匹配
- 使用不包含对象数据的运动文件
- 移除实验配置中的对象配置

## Capabilities

### New Capabilities

- `box-as-terrain`: 将 box 障碍物作为地形加载，而不是单独的 RigidObject 或 Articulation

### Modified Capabilities

- `terrain-loading`: 修改地形加载逻辑，支持从 OBJ 文件加载自定义地形

## Impact

- 训练脚本 `scripts/train_climb_14.sh` 需要修改
- 实验配置 `src/holosoma/holosoma/config_values/wbt/g1/experiment.py` 需要移除对象配置
- 需要生成新的地形文件 `terrain_climb_14_correct.obj`
- 运动文件需要使用不包含对象数据的版本 `climb_14_mj_fps50_no_obj.npz`
