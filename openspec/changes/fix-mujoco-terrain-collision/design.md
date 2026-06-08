## Context

`auto-mujoco-collision-from-obj` 将 OBJ 障碍物提取为 solid box 碰撞体。但 MuJoCo 的 box geom 是实心体积碰撞，与 IsaacSim 中 OBJ 薄壳面碰撞行为不同。机器人脚穿透顶面后被困在实体内部。

当前 `prepare_sim()` 调用 `mj_resetData()` 后通过 `_set_robot_initial_state()` 设置 qpos，但未写入 keyframe。viewer reset 按钮再次调用 `mj_resetData()` 时回到模型默认状态（原点）。

## Goals / Non-Goals

**Goals:**
- 碰撞体行为与 IsaacSim OBJ 薄壳面一致（只阻挡，不困住）
- viewer reset 恢复到配置的 init_state.pos
- 保持自动提取逻辑不变

**Non-Goals:**
- 不改变 MuJoCo 的碰撞检测机制
- 不支持精确的 OBJ 面碰撞（薄壳 box 是合理近似）

## Decisions

### 决策 1：薄壳 box 替代 solid box

将障碍物 box 的 Z 方向 size 缩小为极薄值（如 0.005m），pos 调整到障碍物顶面位置。

**方案 A（推荐）：只保留顶面碰撞**
- 障碍物 box 的 Z size 设为 `SHELL_THICKNESS`（0.005m）
- Z pos 设为 `obstacle_z_max - SHELL_THICKNESS`
- 效果：只有顶面有碰撞，侧面和底面无碰撞
- 脚放在顶面上不会被困住

**方案 B：保留完整轮廓但用薄壳**
- 为每个面创建独立的薄壳 box
- 实现复杂，6 个面需要 6 个 geom

**选择方案 A**：顶面碰撞对 climb 场景足够。侧面碰撞对爬升帮助有限，反而可能干扰。

### 决策 2：keyframe 设置

在 `prepare_sim()` 中，`_set_robot_initial_state()` 之后，调用 `mj_addKeyframe()` 将当前状态保存为 keyframe。

- MuJoCo 的 `mj_resetData()` 会恢复到 keyframe 状态（如果存在）
- 需要在 `root_model` 中添加 keyframe，然后同步到 `root_data`

### 决策 3：薄壳厚度选择

- `SHELL_THICKNESS = 0.005m`（5mm）
- 足够薄以避免困住脚（脚的碰撞几何不会完全嵌入 5mm 厚度）
- 足够厚以确保碰撞检测稳定（MuJoCo 对极薄 geom 可能有数值问题）

## Risks / Trade-offs

- **[风险] 侧面碰撞缺失** → 对 climb 场景影响有限，机器人主要在顶面行走
- **[风险] 薄壳厚度不当** → 5mm 是经验值，可能需要调整
- **[权衡] 精度 vs 简单性** → 薄壳顶面近似比 solid box 更接近 IsaacSim 行为
