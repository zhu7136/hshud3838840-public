## Why

`auto-mujoco-collision-from-obj` 实现的自动碰撞提取生成了 solid box 碰撞体，导致两个问题：

1. **脚卡在平台表面**：平台碰撞体是 Z=0~0.1 的实心 box，机器人脚穿透顶面后被困在实体内部，与 ground plane (Z=0) 形成夹持。IsaacSim 中 OBJ 是薄壳面，无此问题。
2. **reset 后机器人卡在 box 中间**：MuJoCo viewer 的 reset 调用 `mj_resetData()`，但代码未设置 keyframe，机器人回到原点 [0,0,0] 而非配置的 init_state.pos，原点在 climb box 内部。

## What Changes

- 碰撞体从 solid box 改为薄壳 box（厚度极小），模拟 OBJ 薄壳面碰撞行为
- 过滤掉 Z_min=0 且 Z_max 极低的障碍物（与 ground plane 功能重叠的地面层）
- 在 `prepare_sim()` 中设置 MuJoCo keyframe，使 viewer reset 恢复到正确的 init_state.pos

## Capabilities

### New Capabilities
- `thin-shell-obstacle-collision`: 用薄壳 box 替代 solid box，模拟 OBJ 面碰撞
- `mujoco-keyframe-init`: 设置 MuJoCo keyframe 确保 reset 恢复正确初始位置

### Modified Capabilities

（无）

## Impact

- **代码**：`scene_manager.py`（碰撞体生成）、`mujoco.py`（keyframe 设置）
- **兼容性**：只影响 `load_obj` 类型地形，其他类型不受影响
- **风险**：薄壳 box 厚度需要足够小以避免脚嵌入，但不能太小导致碰撞检测不稳定
