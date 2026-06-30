## 1. 新建 Loco 配置目录和文件

- [x] 1.1 创建 `config_values/loco/hu_d04/__init__.py`
- [x] 1.2 创建 `config_values/loco/hu_d04/action.py` — 定义 `hu_d04_29dof_joint_pos`
- [x] 1.3 创建 `config_values/loco/hu_d04/command.py` — 定义 `hu_d04_29dof_command`（LocomotionCommand + LocomotionGait）
- [x] 1.4 创建 `config_values/loco/hu_d04/curriculum.py` — 定义 `hu_d04_29dof_curriculum_fast_sac`（PenaltyCurriculum）
- [x] 1.5 创建 `config_values/loco/hu_d04/experiment.py` — 定义 `hu_d04_29dof_fast_sac` 实验配置
- [x] 1.6 创建 `config_values/loco/hu_d04/observation.py` — 定义 `hu_d04_29dof_loco_single_wolinvel`
- [x] 1.7 创建 `config_values/loco/hu_d04/randomization.py` — 定义 `hu_d04_29dof_randomization`
- [x] 1.8 创建 `config_values/loco/hu_d04/reward.py` — 定义 `hu_d04_29dof_loco_fast_sac`（含 29 个 pose_weights）
- [x] 1.9 创建 `config_values/loco/hu_d04/termination.py` — 定义 `hu_d04_29dof_termination`

## 2. 注册 Presets 到顶层模块

- [x] 2.1 在 `config_values/action.py` 注册 `hu_d04_29dof_joint_pos`
- [x] 2.2 在 `config_values/command.py` 注册 `hu_d04_29dof_command`
- [x] 2.3 在 `config_values/curriculum.py` 注册 `hu_d04_29dof_curriculum_fast_sac`
- [x] 2.4 在 `config_values/observation.py` 注册 `hu_d04_29dof_loco_single_wolinvel`
- [x] 2.5 在 `config_values/randomization.py` 注册 `hu_d04_29dof_randomization`
- [x] 2.6 在 `config_values/reward.py` 注册 `hu_d04_29dof_loco_fast_sac`
- [x] 2.7 在 `config_values/termination.py` 注册 `hu_d04_29dof_termination`

## 3. 注册实验

- [x] 3.1 在 `config_values/experiment.py` 导入并注册 `hu_d04_29dof_fast_sac`

## 4. 验证

- [x] 4.1 运行 `python train_agent.py exp:hu-d04-29dof-loco-fast-sac --help` 确认 CLI 子命令可用
