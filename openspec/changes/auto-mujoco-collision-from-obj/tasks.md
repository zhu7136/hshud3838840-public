## 1. 障碍物提取逻辑

- [x] 1.1 在 `scene_manager.py` 中新增 `_extract_obstacles_from_mesh()` 方法，基于 Z 高度分层提取独立障碍物区域
- [x] 1.2 实现 bounding box 计算：为每个障碍物区域计算轴对齐的 pos 和 size
- [x] 1.3 支持多障碍物：返回障碍物列表而非单个障碍物

## 2. 配置参数支持

- [x] 2.1 在 terrain config 中添加 `ground_z_threshold` 参数（默认 0.01m）
- [x] 2.2 将阈值参数传递到 `_create_trimesh()` 方法

## 3. 碰撞体生成重构

- [x] 3.1 修改 `_create_trimesh()` 调用 `_extract_obstacles_from_mesh()` 获取障碍物列表
- [x] 3.2 为每个障碍物动态生成 MuJoCo box geom（替代硬编码的 `terrain_obstacle`）
- [x] 3.3 保留 `terrain_ground` plane geom 不变

## 4. 验证

- [x] 4.1 用 `terrain_climb_14_50cm.obj` 验证提取出 2 个障碍物（0.5m climb box + 0.1m 平台）
- [x] 4.2 验证提取的 box 参数与手工计算一致
- [x] 4.3 验证非 `load_obj` 类型地形不受影响
