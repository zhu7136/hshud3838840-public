## 1. 环境检查与验证

- [x] 1.1 验证 climb_14_assets/ 是否包含所有 z_scale (0.8-1.2) 的 URDF 文件
- [x] 1.2 检查预转换的 climb_14_mj_fps50.npz 数据完整性
- [x] 1.3 确认 IsaacSim 环境可访问

## 2. 训练脚本开发

- [x] 2.1 创建 `scripts/train_climb_14.sh` 入口脚本
- [x] 2.2 实现 z_scale 参数解析和验证 (0.8-1.2)
- [x] 2.3 实现环境依赖检查 (conda, GPU, IsaacSim)
- [x] 2.4 集成现有的 `g1_29dof_wbt_fast_sac_climb` 实验预设
- [x] 2.5 实现 motion_file 和 terrain URDF 路径自动关联

## 3. Checkpoint 管理

- [x] 3.1 实现 `--resume` 参数，查找最近的 climb_14 checkpoint
- [x] 3.2 实现 `--status` 参数，显示训练状态摘要
- [x] 3.3 处理无 checkpoint 时的优雅降级

## 4. 测试与文档

- [x] 4.1 编写单元测试: z_scale 参数验证、路径解析
- [x] 4.2 编写集成测试: 端到端训练启动 (dry-run)
- [x] 4.3 更新 README 或创建 `docs/climb_14_training.md`
