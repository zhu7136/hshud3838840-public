## Context

HU_D04 是一款 29DOF 人形机器人（6 腿关节 + 3 腰关节 + 14 臂关节），已有 WBT 任务配置。现在需要为其创建 Locomotion 速度跟踪任务。

现有参考：G1 和 T1 的 Loco 配置结构完全一致（8 个文件 + __init__），差异仅在参数值。

## Goals / Non-Goals

**Goals:**
- 为 HU_D04 29DOF 创建 FastSAC Locomotion 训练任务
- 遵循现有 G1/T1 的配置文件结构和命名规范
- 在 CLI 中注册为 `exp:hu-d04-29dof-loco-fast-sac`

**Non-Goals:**
- 不创建 PPO 变体（后续按需添加）
- 不创建 31DOF 变体（29DOF 是主力配置）
- 不修改现有 G1/T1 配置

## Decisions

### 1. 仿真器：IsaacGym

Locomotion 任务统一使用 IsaacGym（与 G1/T1 一致）。WBT 用 IsaacSim 是因为需要高级渲染，Loco 不需要。

### 2. 观测缩放参数

参考 T1 而非 G1，因为 HU_D04 与 T1 体量更接近：
- `base_ang_vel` scale=1.0（G1 用 0.25）
- `dof_vel` scale=0.1（G1 用 0.05）
- critic `base_lin_vel` scale=1.0（G1 用 2.0）

### 3. pose_weights 设计

HU_D04 29DOF 关节顺序（来自 robot.py）：
- 索引 0-11：腿部（12 关节）→ 低权重 0.01（允许腿部自由运动）
- 索引 12-14：腰部（3 关节）→ 中权重 1.0
- 索引 15-28：手臂（14 关节）→ 高权重 50.0（保持手臂姿态）

### 4. 奖励结构

与 G1/T1 完全一致的奖励项：tracking_lin_vel、tracking_ang_vel、feet_phase、pose、penalty_*、alive。权重复用 G1 FastSAC 的值作为起点，`alive` 权重=10.0。

### 5. 随机化参数

参考 G1 的随机化范围，适当调整：
- 摩擦系数：[0.5, 1.25]（同 G1）
- 质量随机化：[0.9, 1.2]（同 G1）
- 推力随机化：间隔 [5,10]s，最大速度 1.0

### 6. 实验配置

- 迭代次数：50000（同 G1 FastSAC）
- 项目名：`hv-hu-d04-manager`
- 对称性：启用
- 地形：`terrain_locomotion_mix`

## Risks / Trade-offs

- **[风险] 奖励权重未调优** → 以 G1 FastSAC 权重为起点，训练后根据指标调整
- **[风险] HU_D04 的 PD 增益与 G1 差异大** → 29DOF 配置有独立的 stiffness/damping，随机化范围需验证
