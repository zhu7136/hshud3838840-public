## ADDED Requirements

### Requirement: 障碍物碰撞体使用薄壳而非实心
系统 SHALL 将自动提取的障碍物碰撞体从 solid box 改为薄壳 box，Z 方向 size 设为 SHELL_THICKNESS（0.005m），Z pos 设为障碍物顶面附近。

#### Scenario: 薄壳顶面碰撞
- **WHEN** OBJ 文件包含一个 0.5m 高的障碍物（Z=0~0.5）
- **THEN** 生成的 MuJoCo box geom 的 Z pos = 0.4975, Z size = 0.005（顶面在 Z=0.5）

#### Scenario: 脚不被困住
- **WHEN** 机器人脚放置在薄壳障碍物顶面
- **THEN** 脚不会穿透并被困在碰撞体内部

### Requirement: XY 方向保持原始尺寸
系统 SHALL 保持障碍物 XY 方向的 bounding box 尺寸不变，只缩小 Z 方向。

#### Scenario: XY 尺寸不变
- **WHEN** 障碍物 XY bounding box half-size 为 [0.893, 0.660]
- **THEN** 生成的 MuJoCo box geom 的 XY size 仍为 [0.893, 0.660]
