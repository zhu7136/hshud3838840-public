## 1. 薄壳碰撞体

- [x] 1.1 在 `scene_manager.py` 中定义 `SHELL_THICKNESS = 0.005` 常量
- [x] 1.2 修改 `_extract_obstacles_from_mesh()` 返回值增加 `z_max` 字段
- [x] 1.3 修改 `_create_trimesh()` 中 box geom 生成逻辑：Z size = SHELL_THICKNESS, Z pos = z_max - SHELL_THICKNESS

## 2. MuJoCo keyframe

- [x] 2.1 在 `prepare_sim()` 中 `_set_robot_initial_state()` 之后调用 `mj_addKeyframe()` 保存当前状态
- [x] 2.2 验证 viewer reset 按钮恢复到 init_state.pos

## 3. 验证

- [x] 3.1 验证 climb box 碰撞体：Z pos ≈ 0.4975, Z size = 0.005
- [x] 3.2 验证 platform 碰撞体：Z pos ≈ 0.0975, Z size = 0.005
- [x] 3.3 验证机器人脚不被困在平台表面
