## Context

HU_D04 URDF 的关节链中，left_hip_pitch_link 相对于 base_link 的偏移为 `(0.017, 0.128, 0.008)` — Y=0.128 是侧向偏移，Z=0.008 几乎为零。在 Z-up 系统中，这意味着髋关节几乎与 base 同高，腿部横向伸出。

对比 G1 URDF：left_hip 偏移为 `(0, 0.064, -0.103)` — Z=-0.103 是向下偏移，符合 Z-up 人形机器人结构。

MJCF 已通过 inertial quaternion（`quat="0.613 0.613 -0.353 0.353"` ≈ 90° 旋转）隐式完成了坐标变换，但 URDF 没有。

## Goals / Non-Goals

**Goals:**
- 使 HU_D04 URDF 在 IsaacSim 中正确站立（Z-up）
- 使脚在地面上方而非下方
- 保持 MuJoCo 训练管线兼容

**Non-Goals:**
- 不重新生成 URDF（只做最小修改）
- 不修改 MJCF 的世界坐标系（已正确）

## Decisions

### D1: 在 URDF 中插入 base_footprint 中间 link

**选择**: 添加 `base_footprint` link 作为浮动基座的 child，对 `base_link` 施加 R_x(-90°)

**理由**:
- 最小侵入：不修改现有 link/joint 的相对关系
- 标准做法：ROS URDF 惯例使用 base_footprint 作为浮动基座
- 可逆：只需删除或修改一个 joint

**实现**:
```xml
<link name="base_footprint"/>
<joint name="floating_base_joint" type="floating">
  <parent link="world"/>
  <child link="base_footprint"/>
</joint>
<joint name="base_link_joint" type="fixed">
  <parent link="base_footprint"/>
  <child link="base_link"/>
  <origin xyz="0 0 0" rpy="-1.5707963 0 0"/>  <!-- R_x(-90°) -->
</joint>
```

旋转效果：Y-up → Z-up
- 原 Y 轴 → 新 Z 轴（向上）
- 原 Z 轴 → 新 -Y 轴

### D2: 初始高度调整

**选择**: init_z 从 0.85 调整到 1.0

**理由**:
- base→foot 距离 ≈ 0.91m（MuJoCo 测量）
- init_z=1.0 时 foot_z ≈ 0.09（在地面上方）
- 旋转后距离可能变化，需要重新测量

### D3: MuJoCo XML 同步修改

**选择**: 在 MJCF 的 base_link body 上添加 `euler="-1.5708 0 0"` 旋转

**理由**: 保持 MJCF 和 URDF 的坐标系一致，避免训练时出现不一致

## Risks / Trade-offs

- **[旋转后运动学变化]** → R_x(-90°) 后，关节轴方向改变。hip_pitch 的轴从 Y 变为 Z。需要验证 MuJoCo FK 输出仍然合理
- **[转换脚本需要更新]** → `convert_g1_to_hu_d04.py` 的坐标变换可能需要调整
- **[body_names 可能变化]** → 插入 base_footprint 后 body 数量从 43 变为 44，需要更新 RobotConfig
