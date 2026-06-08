## Why

Holosoma 当前只支持 G1 和 T1 两款人形机器人。LimX Dynamics 的 HU_D04 是一款 31 DOF 全尺寸人形机器人，具备头部关节和 Achilles 腱平行连杆机构。需要将其接入训练管线，使其能够学习已有的 climbing 动作（climb_14），验证 holosoma 对不同机器人平台的泛化能力。

## What Changes

- 将 HU_D04 模型文件（URDF/MJCF/STL）复制到 `data/robots/hu_d04/`
- 编写 G1→HU_D04 关节重映射脚本，处理：
  - 头部 2 DOF 插入（G1 无头部关节）
  - 腕部 roll↔yaw 顺序反转（G1: roll-pitch-yaw → HU_D04: yaw-pitch-roll）
  - 通过 MuJoCo FK 计算 body kinematics，输出 holosoma NPZ
- 在 `config_values/robot.py` 注册 `hu_d04_31dof` 机器人配置（关节限位、力矩、PD 增益、对称映射）
- 创建 HU_D04 的 WBT 实验配置（observation、action、reward、termination、command、randomization）
- 在 `config_values/experiment.py` 注册实验预设

## Capabilities

### New Capabilities
- `hu-d04-robot-config`: HU_D04 机器人在 holosoma 中的完整注册——模型文件、RobotConfig、关节/body 定义、PD 增益、对称映射
- `g1-to-hu-d04-motion-conversion`: G1 OmniRetarget qpos 到 HU_D04 holosoma NPZ 的转换管线——关节重映射 + MuJoCo FK
- `hu-d04-wbt-experiment`: HU_D04 全身跟踪实验配置——observation、action、reward、termination、command、curriculum、randomization 预设

### Modified Capabilities
<!-- 无需修改已有 spec -->

## Impact

- **新增文件**：`data/robots/hu_d04/` 目录（URDF、MJCF、meshes）、转换脚本、`config_values/wbt/hu_d04/` 配置目录
- **修改文件**：`config_values/robot.py`（注册新 robot）、`config_values/experiment.py`（注册新 experiment）
- **依赖**：MuJoCo（FK 转换）、IsaacSim（训练）
- **数据流**：新增 G1 NPZ → 重映射 → MuJoCo FK → HU_D04 holosoma NPZ 的转换管线
