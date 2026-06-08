## Why

HU_D04 的 URDF 使用 Y-up 坐标系（ROS/Gazebo 标准），但 IsaacSim 期望 Z-up。加载后机器人旋转 90° 侧躺在地上，且 init_z=0.85 低于 base→foot 距离（~0.91m），导致脚在地板以下。

## What Changes

- 在 URDF 中插入 `base_footprint` link 作为浮动基座的 child，对 `base_link` 施加 R_x(-90°) 旋转，将 Y-up 转换为 Z-up
- 调整 `init_state.pos` 的 Z 值，使脚正确接触地面
- 同步修改 MuJoCo XML 的 worldbody 旋转（保持 MuJoCo 训练一致性）
- 更新 `convert_g1_to_hu_d04.py` 中的坐标变换逻辑

## Capabilities

### New Capabilities
<!-- 无新增能力 -->

### Modified Capabilities
- `hu-d04-robot-config`: 修复 URDF 坐标系和初始高度

## Impact

- **修改文件**：`data/robots/hu_d04/hu_d04_31dof.urdf`、`data/robots/hu_d04/hu_d04_31dof.xml`、`config_values/robot.py`（init_pos）、`convert_g1_to_hu_d04.py`
- **风险**：旋转后需要验证 MuJoCo FK 和训练管线仍正常工作
