## 1. 坐标修正方案探索

- [x] 1.1 尝试 URDF base_footprint + fixed joint R_x(-90°) → 无效
- [x] 1.2 尝试 MJCF body euler → 无效
- [x] 1.3 尝试 init_state.rot → 无效
- [x] 1.4 找到根因：IsaacLab UrdfConverter 缺少 `set_up_vector(0, 0, 1)` 调用

## 2. 修复

- [x] 2.1 在 IsaacLab `urdf_converter.py` 的 `_get_urdf_import_config()` 中添加 `import_config.set_up_vector(0, 0, 1)`
- [x] 2.2 回退 init_state.rot 修改
- [x] 2.3 确认 init_state.pos[2]=1.0（脚在地面上方）

## 3. 验证

- [ ] 3.1 在 IsaacSim 中测试：机器人是否直立
- [ ] 3.2 验证地形正确加载
