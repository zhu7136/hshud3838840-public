## Why

Holosoma 已有完整的 WBT (Whole-Body Tracking) 训练框架，但针对 climb_14 地形攀爬动作的训练流程分散在文档和示例中，缺乏统一的端到端指南。新用户需要一个清晰的流程来：(1) 转换 OmniRetarget 数据，(2) 配置训练参数，(3) 启动训练并监控。

## What Changes

- 创建 climb_14 训练的端到端脚本，整合数据转换、配置生成、训练启动
- 添加配置预设，支持不同 z_scale 参数 (0.8-1.2)
- 集成 WandB 日志和checkpoint管理
- 添加训练状态监控和自动恢复机制

## Capabilities

### New Capabilities

- `climb-training-pipeline`: climb_14 动作的完整训练流程，包括数据转换、配置管理、训练执行和监控

### Modified Capabilities

(无现有 capability 需要修改)

## Impact

- 新增训练脚本: `scripts/train_climb_14.sh` 或 Python 入口
- 配置文件: `src/holosoma/holosoma/config_values/wbt/g1/climb_14_presets.py`
- 依赖: 现有依赖已满足 (holosoma, holosoma_retargeting, IsaacSim)
- 文档: 需要更新 README 或添加独立训练指南
