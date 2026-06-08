## ADDED Requirements

### Requirement: 一键启动 climb_14 训练

系统 SHALL 提供单一命令启动 climb_14 地形攀爬训练，无需手动指定多个配置参数。

#### Scenario: 使用默认配置启动训练

- **WHEN** 用户执行 `scripts/train_climb_14.sh` (无参数)
- **THEN** 系统使用 z_scale=1.0、FastSAC 算法、IsaacSim 仿真器启动训练

#### Scenario: 指定 z_scale 参数

- **WHEN** 用户执行 `scripts/train_climb_14.sh --z_scale 1.2`
- **THEN** 系统加载 climb_14_z_scale_1.2 对应的 motion 数据和 terrain URDF

### Requirement: z_scale 参数化

系统 SHALL 支持 z_scale 参数 (0.8, 0.9, 1.0, 1.1, 1.2)，自动选择对应的 motion 数据和 terrain 资产。

#### Scenario: z_scale 参数验证

- **WHEN** 用户指定 z_scale=1.5 (超出范围)
- **THEN** 系统报错并显示支持的 z_scale 值列表

#### Scenario: 自动关联 terrain 资产

- **WHEN** 用户指定 z_scale=0.9
- **THEN** 系统自动加载 `climb_14_assets/multi_boxes_z_scale_0.9.urdf` 作为 terrain

### Requirement: Checkpoint 自动恢复

系统 SHALL 支持从最近的 checkpoint 恢复训练，避免意外中断导致的进度丢失。

#### Scenario: 从 checkpoint 恢复

- **WHEN** 用户执行 `scripts/train_climb_14.sh --resume`
- **THEN** 系统查找 `logs/WholeBodyTracking/` 下最近的 climb_14 训练 checkpoint 并恢复

#### Scenario: 无 checkpoint 时正常启动

- **WHEN** 用户执行 `scripts/train_climb_14.sh --resume` 但无历史 checkpoint
- **THEN** 系统从头开始训练并给出提示

### Requirement: 训练状态监控

系统 SHALL 提供训练状态查询，包括当前 epoch、reward、checkpoint 路径。

#### Scenario: 查询训练状态

- **WHEN** 用户执行 `scripts/train_climb_14.sh --status`
- **THEN** 系统显示最近一次训练的 epoch、平均 reward、最新 checkpoint 路径

### Requirement: 环境依赖检查

系统 SHALL 在启动训练前检查必要的环境依赖 (conda 环境、IsaacSim、GPU)。

#### Scenario: 缺少 conda 环境

- **WHEN** 用户未激活 hssim 环境
- **THEN** 系统报错并提示 `conda activate hssim`

#### Scenario: GPU 不可用

- **WHEN** 系统无可用 GPU 或 CUDA 不可用
- **THEN** 系统报错并提示检查 GPU 驱动和 CUDA 安装
