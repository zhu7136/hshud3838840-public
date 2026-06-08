## ADDED Requirements

### Requirement: HU_D04 模型文件放置
系统 SHALL 在 `data/robots/hu_d04/` 目录下包含 HU_D04 的 MuJoCo XML 文件（`hu_d04_31dof.xml`，基于 `HU_D04_01_gmr.xml`）及其 STL 网格文件。XML 文件 MUST 使用直驱 ankle_pitch/ankle_roll 关节（非 achilles 连杆）。

#### Scenario: 模型文件可被 MuJoCo 加载
- **WHEN** 调用 `mujoco.MjModel.from_xml_path("data/robots/hu_d04/hu_d04_31dof.xml")`
- **THEN** 成功加载，模型包含 31 个 actuated hinge 关节，无 ball 关节，无 equality 约束

#### Scenario: 模型文件可被 IsaacSim URDF 转换器加载
- **WHEN** IsaacSim 的 `UrdfFileCfg` 引用 `hu_d04/hu_d04_31dof.urdf`
- **THEN** 成功转换为 USD 并加载到仿真环境

### Requirement: HU_D04 RobotConfig 注册
`config_values/robot.py` 的 `DEFAULTS` 字典 SHALL 包含键 `"hu_d04_31dof"`，其值为完整的 `RobotConfig` 实例。

#### Scenario: RobotConfig 包含正确的关节定义
- **WHEN** 访问 `DEFAULTS["hu_d04_31dof"].dof_names`
- **THEN** 返回 31 个关节名列表，顺序与 MJCF actuator 顺序一致：左腿6 → 右腿6 → 腰部3 → 头部2 → 左臂7 → 右臂7

#### Scenario: RobotConfig 包含正确的 body 定义
- **WHEN** 访问 `DEFAULTS["hu_d04_31dof"].body_names`
- **THEN** 返回与 HU_D04 URDF 的 link 名称完全一致的列表

#### Scenario: RobotConfig 包含关节限位
- **WHEN** 访问 `dof_pos_lower_limit_list` 和 `dof_pos_upper_limit_list`
- **THEN** 每个关节的限位与 URDF 中 `<limit>` 标签定义一致

#### Scenario: RobotConfig 包含力矩限制
- **WHEN** 访问 `dof_effort_limit_list`
- **THEN** 每个关节的力矩与 SRDF 中 `gear_ratio × rated_torque` 推算值一致

#### Scenario: RobotConfig 包含对称映射
- **WHEN** 访问 `symmetry_joint_names`
- **THEN** 包含 left/right 关节对的映射（如 `left_hip_pitch_joint` ↔ `right_hip_pitch_joint`）

### Requirement: HU_D04 PD 控制增益
`RobotControlConfig` SHALL 为每个关节组提供 `stiffness` 和 `damping` 值。增益 MUST 基于 SRDF 的 rotor_inertia 和 gear_ratio 推算。

#### Scenario: PD 增益覆盖所有关节组
- **WHEN** 访问 `control.stiffness` 字典
- **THEN** 包含以下关节组的增益：`hip_pitch`, `hip_roll`, `hip_yaw`, `knee`, `ankle_pitch`, `ankle_roll`, `waist_yaw`, `waist_roll`, `waist_pitch`, `head_yaw`, `head_pitch`, `shoulder_pitch`, `shoulder_roll`, `shoulder_yaw`, `elbow`, `wrist_yaw`, `wrist_pitch`, `wrist_roll`
