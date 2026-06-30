## Why

HU_D04 人形机器人目前只有 Whole-Body Tracking（动捕跟踪）训练任务，缺少 Locomotion（速度跟踪）能力。速度跟踪是机器人自主移动的基础能力，需要补齐。

## What Changes

- 新建 `config_values/loco/hu_d04/` 目录，包含 9 个配置文件（action、command、curriculum、experiment、observation、randomization、reward、termination、__init__）
- 注册 `hu_d04_29dof_loco_fast_sac` 实验到 `experiment.py` 的 DEFAULTS
- 在 7 个顶层 config 模块（action、command、curriculum、observation、randomization、reward、termination）中注册新的 HU_D04 loco presets

## Capabilities

### New Capabilities

- `hu-d04-locomotion`: HU_D04 29DOF 机器人的速度跟踪（Locomotion）训练任务，使用 FastSAC 算法，基于 IsaacGym 仿真器

### Modified Capabilities

（无）

## Impact

- 新增文件：`config_values/loco/hu_d04/` 下 9 个文件
- 修改文件：`config_values/experiment.py` 及 7 个顶层 config 模块
- CLI 新增子命令：`exp:hu-d04-29dof-loco-fast-sac`
