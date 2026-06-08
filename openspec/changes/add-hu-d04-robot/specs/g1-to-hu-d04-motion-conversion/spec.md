## ADDED Requirements

### Requirement: 关节重映射脚本
系统 SHALL 提供一个 Python 脚本 `convert_g1_to_hu_d04.py`，将 G1 OmniRetarget 格式的 qpos NPZ 转换为 HU_D04 的 holosoma NPZ。

#### Scenario: 输入格式
- **WHEN** 脚本接收一个 NPZ 文件，包含 `qpos`（shape `[T, 36]`，布局 `[quat(4), pos(3), joints(29)]`）和 `fps`
- **THEN** 脚本能正确解析输入数据

#### Scenario: 关节重映射——腿部和腰部
- **WHEN** G1 qpos 的关节部分 `[0:15]` 包含左腿6 + 右腿6 + 腰部3
- **THEN** HU_D04 qpos 的关节部分 `[0:15]` 与 G1 完全一致

#### Scenario: 关节重映射——头部插入
- **WHEN** G1 没有头部关节
- **THEN** HU_D04 qpos 的关节部分 `[15:17]`（head_yaw, head_pitch）填 0

#### Scenario: 关节重映射——肩部和肘部
- **WHEN** G1 qpos 的关节部分 `[15:19]` 和 `[22:26]` 包含左右肩部3 + elbow
- **THEN** HU_D04 qpos 的关节部分 `[17:21]` 和 `[24:28]` 与 G1 对应位置一致

#### Scenario: 关节重映射——腕部 roll↔yaw 交换
- **WHEN** G1 腕部顺序为 `[wrist_roll, wrist_pitch, wrist_yaw]`
- **THEN** HU_D04 腕部顺序为 `[wrist_yaw, wrist_pitch, wrist_roll]`，即 G1[19]→HU_D04[21]，G1[20]→HU_D04[22]，G1[21]→HU_D04[23]（右侧同理）

#### Scenario: 输出格式
- **WHEN** 脚本完成转换
- **THEN** 输出一个中间 NPZ 文件，包含重映射后的 qpos（shape `[T, 38]`，布局 `[quat(4), pos(3), joints(31)]`）和原始 fps

### Requirement: MuJoCo FK 计算 body kinematics
系统 SHALL 使用 MuJoCo forward kinematics 计算 HU_D04 每个 body 的世界坐标位置、朝向和速度。

#### Scenario: 使用 HU_D04 模型进行 FK
- **WHEN** 将重映射后的 qpos 逐帧设置到 HU_D04 MuJoCo 模型并调用 `mj_forward`
- **THEN** 正确计算 `body_pos_w`（`[T, nbody, 3]`）、`body_quat_w`（`[T, nbody, 4]`）、`body_lin_vel_w`（`[T, nbody, 3]`）、`body_ang_vel_w`（`[T, nbody, 3]`）

#### Scenario: body_names 和 joint_names 从模型自动提取
- **WHEN** FK 计算完成
- **THEN** 输出 NPZ 中的 `body_names` 和 `joint_names` 直接从 MuJoCo 模型读取，与 URDF 一致

### Requirement: 输出 holosoma NPZ
转换管线 SHALL 输出符合 holosoma `MotionLoader` 要求的 NPZ 文件。

#### Scenario: NPZ 包含所有必需 key
- **WHEN** 加载输出 NPZ
- **THEN** 包含以下 key：`fps`, `joint_names`（31个）, `body_names`, `joint_pos`（`[T, 38]`：7 root + 31 joints）, `joint_vel`（`[T, 37]`：6 root + 31 joints）, `body_pos_w`, `body_quat_w`, `body_lin_vel_w`, `body_ang_vel_w`

#### Scenario: MotionLoader 能加载输出文件
- **WHEN** holosoma 的 `MotionLoader` 加载输出 NPZ
- **THEN** 所有 body_names 和 joint_names 与 HU_D04 robot config 匹配，不报错
