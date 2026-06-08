## Context

当前 climb_14 训练配置存在两个问题：
1. box 障碍物作为单独的 RigidObject 或 Articulation 加载时无法正确固定在地面
2. 地形文件中的 box 高度与实际模型不匹配

现有系统支持通过 `terrain:terrain-load-obj` 配置加载 OBJ 文件作为地形。

## Goals / Non-Goals

**Goals:**
- box 障碍物作为地形固定在地面
- 地形文件中的 box 高度与实际模型匹配
- 动作文件与地形正确配合

**Non-Goals:**
- 支持 box 作为动态对象（非固定）
- 修改地形加载的核心逻辑

## Decisions

**Decision 1: 将 box 作为地形加载**
- 方案 A: 使用 RigidObject + fix_base（已尝试，失败）
- 方案 B: 使用 Articulation + fix_root_link（已尝试，失败）
- 方案 C: 将 box 作为地形加载（✅ 选择）
- 理由: 地形加载方式可以确保 box 完全固定，且与现有地形系统兼容

**Decision 2: 生成正确的地形文件**
- 方案 A: 使用现有的 terrain_climb_14_with_boxes.obj（高度不正确）
- 方案 B: 从 box 模型重新生成地形文件（✅ 选择）
- 理由: 确保 box 高度与实际模型匹配（0.64 米）

**Decision 3: 使用不包含对象数据的运动文件**
- 方案 A: 使用包含对象数据的运动文件（需要加载对象）
- 方案 B: 使用不包含对象数据的运动文件（✅ 选择）
- 理由: 避免代码尝试加载不存在的对象

## Risks / Trade-offs

**Risk 1: 地形文件需要手动更新**
- 影响: 如果 box 模型变化，需要重新生成地形文件
- 缓解: 提供地形生成脚本

**Risk 2: 失去对象动态交互能力**
- 影响: box 无法移动或与机器人动态交互
- 缓解: 当前需求是固定 box，不需要动态交互
