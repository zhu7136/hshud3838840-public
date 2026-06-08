## Why

MuJoCo 地形加载中，OBJ 文件仅作为视觉几何，碰撞由硬编码的 box geom 代替。这导致两个问题：

1. **手动维护成本高**：每次修改地形 OBJ 文件，都需要同步更新 `scene_manager.py` 中的硬编码碰撞参数（位置、尺寸）。
2. **地形复现不完整**：当前 `terrain_climb_14_50cm.obj` 包含两个障碍物，但 MuJoCo 只硬编码了一个 box 碰撞体，0.1m 高的条形平台完全缺失碰撞。sim2sim 时 MuJoCo 中 5x5m 区域的地形与 IsaacSim 训练场景不一致。

## What Changes

- 新增从 OBJ 文件自动提取碰撞几何的逻辑，替代硬编码 box geom
- OBJ 障碍物自动分解为多个凸 box 进行碰撞近似
- 移除 `_create_trimesh()` 中硬编码的 `terrain_obstacle` box geom
- 保持地面平面（`terrain_ground`）不变，因其为通用基础碰撞

## Capabilities

### New Capabilities
- `obj-collision-extraction`: 从 OBJ 文件自动提取障碍物几何，生成 MuJoCo box 碰撞体集合

### Modified Capabilities

（无现有 spec 需要修改）

## Impact

- **代码**：`src/holosoma/holosoma/simulator/mujoco/scene_manager.py` — `_create_trimesh()` 方法重写
- **依赖**：可能引入 `trimesh` 的凸分解能力（已在项目依赖中）
- **兼容性**：需要确保非 `load_obj` 类型的地形不受影响
- **风险**：自动分解的凸包近似精度可能不如手工调优，需要验证 sim2sim 一致性
