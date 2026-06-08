## ADDED Requirements

### Requirement: Box obstacles as terrain

系统 SHALL 支持将 box 障碍物作为地形加载，而不是单独的 RigidObject 或 Articulation。

#### Scenario: Box loaded as terrain
- **WHEN** 训练配置指定 `terrain:terrain-load-obj` 并提供包含 box 的 OBJ 文件
- **THEN** 系统将 box 作为地形的一部分加载，box 固定在地面

### Requirement: Correct box height

地形文件中的 box 高度 SHALL 与实际 box 模型高度匹配。

#### Scenario: Terrain box height matches model
- **WHEN** 生成地形文件时使用 box 模型
- **THEN** 地形文件中的 box 高度与 box 模型高度一致（0.64 米）

### Requirement: Motion file without object data

训练 SHALL 使用不包含对象数据的运动文件。

#### Scenario: Motion file has no object data
- **WHEN** 运动文件不包含 `object_pos_w` 数据
- **THEN** 代码不会尝试加载对象，训练正常进行

### Requirement: Foot position matches box position

动作文件中的脚部位置 SHALL 与地形中的 box 位置匹配，确保机器人能够踩到 box 上。

#### Scenario: Foot can reach box top
- **WHEN** 动作文件中的脚部轨迹与 box 位置匹配
- **THEN** 脚部最高点 >= box 最高点（0.64 米）

#### Scenario: Foot trajectory overlaps box area
- **WHEN** 分析脚部轨迹
- **THEN** 存在脚部在 box 附近的帧（Z ∈ [0.50, 0.64]）

### Requirement: Robot initial position

机器人初始位置 SHALL 与动作文件中的初始位置匹配。

#### Scenario: Initial position matches motion file
- **WHEN** 配置中的初始位置与动作文件中的初始位置比较
- **THEN** 差异 <= 0.10 米
