## ADDED Requirements

### Requirement: 自动从 OBJ 提取障碍物碰撞几何
系统 SHALL 从 OBJ 地形文件中自动提取高于地面的障碍物区域，并为每个独立障碍物生成 MuJoCo box 碰撞体。

#### Scenario: 单个障碍物提取
- **WHEN** OBJ 文件包含一个高于 `ground_z_threshold` 的障碍物
- **THEN** 系统生成一个 MuJoCo box geom，pos 为障碍物 bounding box 中心，size 为 bounding box 半尺寸

#### Scenario: 多个障碍物提取
- **WHEN** OBJ 文件包含多个空间分离的障碍物（Z > `ground_z_threshold`）
- **THEN** 系统为每个独立障碍物分别生成 MuJoCo box geom

#### Scenario: 无障碍物
- **WHEN** OBJ 文件中没有高于 `ground_z_threshold` 的几何
- **THEN** 系统不生成额外的 box geom，仅保留 ground plane

### Requirement: 障碍物检测阈值可配置
系统 SHALL 支持通过 terrain config 配置障碍物检测的阈值参数。

#### Scenario: 自定义阈值
- **WHEN** 用户通过 config 设置 `ground_z_threshold=0.02`
- **THEN** 系统使用 0.02m 作为地面/障碍物分界线

#### Scenario: 默认阈值
- **WHEN** 用户未指定阈值参数
- **THEN** 系统使用默认值 `ground_z_threshold=0.01m`

### Requirement: 保留 ground plane 碰撞
系统 SHALL 保留 Z=0 处的 ground plane 碰撞体，不受自动提取逻辑影响。

#### Scenario: ground plane 始终存在
- **WHEN** 使用 `load_obj` 类型地形
- **THEN** MuJoCo scene 中始终包含 `terrain_ground` plane geom

### Requirement: 移除硬编码碰撞体
系统 SHALL 移除 `_create_trimesh()` 中硬编码的 `terrain_obstacle` box geom。

#### Scenario: 硬编码 box 被替换
- **WHEN** 加载 `load_obj` 类型地形
- **THEN** scene 中不再包含名为 `terrain_obstacle` 的硬编码 geom

#### Scenario: 向后兼容
- **WHEN** 加载非 `load_obj` 类型地形（如 `trimesh`、`hfield`）
- **THEN** 现有行为不受影响
