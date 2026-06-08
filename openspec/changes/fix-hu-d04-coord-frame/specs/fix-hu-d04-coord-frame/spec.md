## ADDED Requirements

### Requirement: URDF 坐标系修正
`hu_d04_31dof.urdf` SHALL 使用 Z-up 坐标系，通过在浮动基座和 base_link 之间插入 `base_footprint` link 和 R_x(-90°) 固定关节实现。

#### Scenario: 机器人在 IsaacSim 中直立
- **WHEN** IsaacSim 加载 URDF 并设置 init_pos=[0,0,1.0]、init_rot=[0,0,0,1]
- **THEN** 机器人直立站立，脚在地面上方

#### Scenario: base→foot 距离正确
- **WHEN** 在 MuJoCo 中设置默认站姿
- **THEN** contact_foot_center 的 Z 坐标 > 0（在地面上方）

### Requirement: 初始高度修正
`config_values/robot.py` 中 `hu_d04_31dof.init_state.pos[2]` SHALL 设置为使脚正确接触地面的值（约 1.0）。

#### Scenario: 脚不在地下
- **WHEN** 环境初始化
- **THEN** 所有脚部 body 的 Z 坐标 ≥ 0

### Requirement: MuJoCo XML 同步
`hu_d04_31dof.xml` 的 base_link body SHALL 包含与 URDF 一致的坐标旋转。

#### Scenario: MJCF 和 URDF 运动学一致
- **WHEN** 对同一组 qpos 分别用 MJCF 和 URDF（通过 IsaacSim）计算 FK
- **THEN** body 位置差异 < 1mm

### Requirement: 转换脚本兼容
`convert_g1_to_hu_d04.py` SHALL 在坐标旋转后仍能正确生成 holosoma NPZ。

#### Scenario: 转换后 body 位置合理
- **WHEN** 运行转换脚本
- **THEN** 输出 NPZ 的 body_pos_w 中，脚部 Z 坐标在合理范围内（地面附近）
