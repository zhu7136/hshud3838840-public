## ADDED Requirements

### Requirement: Load terrain from OBJ file

系统 SHALL 支持从 OBJ 文件加载自定义地形。

#### Scenario: Load OBJ terrain
- **WHEN** 配置指定 `mesh_type: "load_obj"` 并提供 OBJ 文件路径
- **THEN** 系统加载 OBJ 文件作为地形

### Requirement: Terrain file validation

系统 SHALL 验证地形文件的存在和有效性。

#### Scenario: Terrain file exists
- **WHEN** 指定的地形文件存在且格式正确
- **THEN** 系统成功加载地形

#### Scenario: Terrain file not found
- **WHEN** 指定的地形文件不存在
- **THEN** 系统抛出 FileNotFoundError

### Requirement: Terrain mesh properties

地形网格 SHALL 包含正确的物理属性。

#### Scenario: Terrain has collision geometry
- **WHEN** 地形加载完成
- **THEN** 地形具有碰撞几何体，可以与机器人交互
