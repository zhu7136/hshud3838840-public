## ADDED Requirements

### Requirement: HU_D04 Locomotion 训练任务可通过 CLI 启动

系统 SHALL 支持通过 `exp:hu-d04-29dof-loco-fast-sac` 子命令启动 HU_D04 29DOF 速度跟踪训练。

#### Scenario: 使用 CLI 启动训练
- **WHEN** 用户执行 `python train_agent.py exp:hu-d04-29dof-loco-fast-sac`
- **THEN** 系统使用 FastSAC 算法、IsaacGym 仿真器、HU_D04 29DOF 机器人配置启动 Locomotion 训练

### Requirement: HU_D04 Locomotion 使用速度跟踪观测空间

观测空间 SHALL 包含 base_ang_vel、projected_gravity、command_lin_vel、command_ang_vel、dof_pos、dof_vel、actions、sin_phase、cos_phase（actor）及 base_lin_vel（critic）。

#### Scenario: Actor 观测维度正确
- **WHEN** 训练环境初始化
- **THEN** actor_obs 包含 9 个观测项，维度与 HU_D04 29DOF 关节数匹配

### Requirement: HU_D04 Locomotion 奖励函数包含速度跟踪项

奖励 SHALL 包含 tracking_lin_vel、tracking_ang_vel、feet_phase、pose、penalty_ang_vel_xy、penalty_orientation、penalty_action_rate、penalty_close_feet_xy、penalty_feet_ori、alive。

#### Scenario: 奖励计算正确
- **WHEN** 环境执行一步
- **THEN** 总奖励为所有奖励项加权和

### Requirement: HU_D04 Locomotion 终止条件包含接触力超限和超时

终止条件 SHALL 包含 contact_forces_exceeded 和 timeout_exceeded。

#### Scenario: 接触力超限终止
- **WHEN** 机器人非足部身体接触力超过阈值
- **THEN** episode 终止

### Requirement: HU_D04 Locomotion pose_weights 遵循关节分组权重

pose_weights SHALL 对腿部关节使用低权重（0.01）、腰部使用中权重（1.0）、手臂使用高权重（50.0），共 29 个值。

#### Scenario: pose_weights 数量匹配
- **WHEN** 配置加载
- **THEN** pose_weights 列表长度为 29，与 HU_D04 29DOF 关节数一致
