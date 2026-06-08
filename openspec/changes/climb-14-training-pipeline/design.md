## Context

Holosoma 训练框架已支持 WBT (Whole-Body Tracking) 训练，包括 climb_14 实验预设 (`g1_29dof_wbt_fast_sac_climb`)。当前流程需要手动执行多个步骤：

1. 数据转换: `convert_to_holosoma.py` 或 `convert_data_format_mj.py`
2. 配置覆盖: 命令行参数指定 motion_file 和 terrain
3. 训练启动: `train_agent.py` + 实验预设

预转换数据已存在: `climb_14_mj_fps50.npz` (50fps, MuJoCo FK)

## Goals / Non-Goals

**Goals:**
- 一键启动 climb_14 训练，自动处理配置
- 支持 z_scale 参数化 (0.8, 0.9, 1.0, 1.1, 1.2)
- 集成 checkpoint 管理和训练恢复
- 提供训练状态监控

**Non-Goals:**
- 不修改核心训练算法 (FastSAC/PPO)
- 不实现新的仿真器后端
- 不支持非 climb 类型的动作训练 (保持通用性)

## Decisions

### 1. 脚本语言: Bash + Python 混合

**选择**: Bash 脚本作为入口，调用 Python 配置生成

**理由**:
- 训练启动是 shell 级操作，Bash 更自然
- 配置生成需要 Python 逻辑 (tyro dataclass)
- 与现有 `scripts/` 和 `demo_scripts/` 保持一致

**替代方案**: 纯 Python CLI → 增加复杂度，无明显收益

### 2. 配置管理: 继承现有实验预设

**选择**: 复用 `g1_29dof_wbt_fast_sac_climb`，通过命令行覆盖参数

**理由**:
- 最小化代码改动
- 保持与现有实验配置的兼容性
- 用户可直接参考现有预设理解配置

**替代方案**: 创建独立的 climb_14 配置文件 → 增加维护负担

### 3. 数据路径: 硬编码相对路径 + 环境变量覆盖

**选择**: 默认使用 `holosoma/data/motions/...`，支持 `HOLOSOMA_MOTION_DIR` 环境变量

**理由**:
- 预转换数据已在仓库中，路径稳定
- 环境变量允许用户指向自定义数据
- 符合 holosoma 的路径解析约定

### 4. Checkpoint 管理: 复用 logs/ 目录结构

**选择**: 保持现有 `logs/WholeBodyTracking/<timestamp>-<exp>/` 结构

**理由**:
- 与 IsaacLab/WandB 集成一致
- 支持自动 checkpoint 恢复 (`resume` 参数)
- 无需额外存储管理

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| z_scale 参数化需要对应的 terrain URDF | 检查 `climb_14_assets/` 是否包含所有 z_scale 变体，缺失则需生成 |
| 长时间训练中断 | 利用 FastSAC 的 `resume` 机制自动恢复 |
| IsaacSim 环境依赖 | 脚本添加环境检查，给出明确错误提示 |

## Open Questions

- [ ] `climb_14_assets/` 是否包含所有 z_scale (0.8-1.2) 的 URDF？需要验证
- [ ] 是否需要支持多 GPU 并行训练？当前设计假设单 GPU
- [ ] 训练超参数 (learning rate, batch size) 是否需要针对 climb 场景调优？
