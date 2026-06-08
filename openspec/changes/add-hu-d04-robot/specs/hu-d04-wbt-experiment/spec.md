## ADDED Requirements

### Requirement: HU_D04 WBT 实验预设注册
`config_values/experiment.py` 的 `DEFAULTS` 字典 SHALL 包含键 `"hu_d04_31dof_wbt_fast_sac"`，可作为 `exp:hu-d04-31dof-wbt-fast-sac` 从 CLI 调用。

#### Scenario: 实验预设可被 tyro 解析
- **WHEN** 运行 `python train_agent.py exp:hu-d04-31dof-wbt-fast-sac --help`
- **THEN** tyro 成功解析配置并显示帮助信息，无报错

### Requirement: HU_D04 WBT 观测配置
系统 SHALL 为 HU_D04 创建 WBT 观测配置，actor 观测包含：motion_command, motion_ref_ori_b, base_ang_vel, dof_pos（31维）, dof_vel（31维）, actions（31维）。critic 观测额外包含：motion_ref_pos_b, robot_body_pos_b, robot_body_ori_b, base_lin_vel。

#### Scenario: 观测维度正确
- **WHEN** 环境初始化
- **THEN** actor observation 维度 = motion_command_dim + 3 + 31 + 31 + 31，critic observation 维度额外加上 pos/ori/lin_vel 维度

### Requirement: HU_D04 WBT 动作配置
系统 SHALL 创建 `JointPositionActionTerm` 配置，动作维度为 31，对应 HU_D04 的所有驱动关节。

#### Scenario: 动作空间维度
- **WHEN** 环境创建动作空间
- **THEN** `action_space.shape[0]` == 31

### Requirement: HU_D04 WBT 奖励配置
系统 SHALL 创建 WBT 奖励配置，包含运动跟踪奖励（global ref pos/ori, relative body pos/ori, body lin/ang vel）和正则化奖励（action_rate_l2, limits_dof_pos, undesired_contacts）。

#### Scenario: body_names_to_track 使用 HU_D04 的 body 名称
- **WHEN** 奖励函数计算 tracking reward
- **THEN** `body_names_to_track` 中的名称全部来自 HU_D04 的 body_names 列表

### Requirement: HU_D04 WBT 终止条件
系统 SHALL 创建终止条件配置，包含超时终止和 BadTracking 终止（pos threshold, ori threshold, body pos threshold）。

#### Scenario: 终止条件阈值可配置
- **WHEN** 配置 `BadTrackingZOnly` 终止条件
- **THEN** pos_threshold、ori_threshold、body_pos_threshold 均可独立设置

### Requirement: HU_D04 WBT 命令配置
系统 SHALL 创建 `MotionCommand` 配置，引用转换后的 HU_D04 holosoma NPZ 文件。

#### Scenario: motion_file 指向 HU_D04 NPZ
- **WHEN** 访问 `command.setup_terms.motion_command.params.motion_config.motion_file`
- **THEN** 路径指向 `data/motions/hu_d04_31dof/whole_body_tracking/` 目录下的 NPZ 文件

#### Scenario: body_names_to_track 与 HU_D04 body 匹配
- **WHEN** MotionCommand 加载 NPZ 并建立索引映射
- **THEN** 所有 `body_names_to_track` 中的名称在 NPZ 的 body_names 中找到匹配

### Requirement: HU_D04 WBT 随机化配置
系统 SHALL 创建随机化配置，包含 push randomizer、actuator randomizer（kp/kd）、rigid body material DR（friction）、base COM randomization、action delay buffers。

#### Scenario: 随机化参数范围可配置
- **WHEN** 配置 actuator randomizer
- **THEN** kp/kd 缩放范围为 [0.9, 1.1]（与 G1 配置一致）
