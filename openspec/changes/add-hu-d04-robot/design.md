## Context

Holosoma 训练管线当前支持 G1（29 DOF）和 T1（29 DOF）两款人形机器人。HU_D04 是 LimX Dynamics 的 31 DOF 全尺寸人形机器人，具备：
- 头部 2 DOF（head_yaw, head_pitch）
- 与 G1 相同的腿部/腰部结构（但 hip_pitch 轴有 ~24° 倾斜）
- 腕部运动链顺序反转（G1: roll→pitch→yaw, HU_D04: yaw→pitch→roll）
- Achilles 腱平行连杆机构（gmr.xml 变体已简化为直驱）

目标是让 HU_D04 学习已有的 climb_14 climbing 动作（当前为 G1 的 OmniRetarget 格式）。

## Goals / Non-Goals

**Goals:**
- 将 HU_D04 注册到 holosoma 训练管线
- 将 G1 的 OmniRetarget qpos 数据转换为 HU_D04 可用的 holosoma NPZ
- 使 HU_D04 能使用 `terrain:terrain-load-obj` 进行 climbing WBT 训练

**Non-Goals:**
- 不做完整的 retarget 管线（从人类动作重新 retarget 到 HU_D04）
- 不支持 HU_D04 的原始 achilles 连杆版本（仅用 gmr 简化版）
- 不做手指/抓取相关配置
- 不保证动作质量最优（先跑通再迭代）

## Decisions

### D1: 使用 HU_D04_gmr.xml（31 DOF 直驱）而非原始 MJCF（29 DOF + 连杆）

**选择**: gmr.xml（31 DOF，无连杆）

**理由**:
- 原始版含 achilles 腱平行连杆（4 ball 关节 + equality 约束），总 DOF 49，标准 RL 训练难以处理
- gmr 版去掉连杆，变成纯串联树形拓扑（37 DOF），适合 IsaacSim/MuJoCo 标准训练
- 保留头部 2 DOF，更完整地利用机器人能力

**替代方案**: 创建去掉头部的 29 DOF 版本使关节与 G1 完全同构——但这需要修改 URDF/XML，且丢失了头部能力

### D2: 关节重映射策略——下半身直接复制 + 上半身重排 + 头部填零

**选择**: 硬编码索引映射

**理由**:
- 腿部（12 DOF）和腰部（3 DOF）的关节名称和顺序在 G1 和 HU_D04 中完全一致，可直接复制
- 肩部 + elbow（每臂 4 DOF）名称和顺序一致，直接复制
- 腕部 3 DOF 需要 roll↔yaw 交换（因运动链中位置不同）
- 头部 2 DOF 在 G1 中不存在，填 0（默认角度）

**替代方案**: 用名称匹配自动映射——但腕部同名关节在不同运动链中语义不同，自动映射会产生错误

### D3: 用 MuJoCo FK 而非简化方案计算 body kinematics

**选择**: 用 `convert_data_format_mj.py` 的模式，通过 MuJoCo `mj_forward` 计算

**理由**:
- `convert_to_holosoma.py` 的简化方案（body 位置 = base 位置）对 climbing 动作误差太大
- MuJoCo FK 能正确计算每个 body 的世界坐标位置/朝向/速度
- 已有成熟的 `convert_data_format_mj.py` 脚本可复用

### D4: PD 增益估算策略

**选择**: 基于 SRDF 的 gear_ratio 和 effort limit 推算，参考 G1 的增益模式

**理由**:
- HU_D04 的 SRDF 包含 rotor_inertia 和 gear_ratio
- G1 的 PD 增益公式：stiffness ≈ effort_limit / (gear_ratio * scale_factor)
- 先用估算值跑通，再根据训练表现调整

## Risks / Trade-offs

- **[腕部动作不自然]** → 腕部 roll↔yaw 交换后，物理运动学不等价（父关节不同）。对 climbing 来说手臂主要起平衡作用，影响可能不大。缓解：先观察训练效果，必要时固定腕部为默认角度
- **[hip_pitch 轴倾斜]** → HU_D04 的 hip_pitch 轴有 ~24° 倾斜，G1 的 qpos 直接赋值后腿部姿态可能略有偏差。缓解：MuJoCo FK 会基于 HU_D04 的实际运动链计算 body 位置，训练时 RL 策略会自适应
- **[PD 增益不准]** → 估算的增益可能导致控制响应过快/过慢。缓解：从小 num_envs 开始测试，观察是否出现振荡或跟踪失败
- **[body_names 不匹配]** → MotionLoader 做 name-based 索引映射，NPZ 中的 body_names 必须与 URDF 完全一致。缓解：转换脚本直接从 MuJoCo 模型读取 body_names
