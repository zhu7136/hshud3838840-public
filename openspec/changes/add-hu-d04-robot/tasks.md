## 1. 模型文件准备

- [x] 1.1 创建 `data/robots/hu_d04/` 目录，复制 `HU_D04_01_gmr.xml` 及其 STL 网格文件
- [x] 1.2 从 `HU_D04_01.urdf` 生成 `hu_d04_31dof.urdf`（用于 IsaacSim 运行时 URDF→USD 转换）
- [x] 1.3 验证 MuJoCo 能加载 `hu_d04_31dof.xml`：`mujoco.MjModel.from_xml_path()` 无报错，确认 31 个 actuated hinge 关节

## 2. 关节重映射 + MuJoCo FK 转换脚本

- [x] 2.1 编写 `convert_g1_to_hu_d04.py` 脚本，实现 G1→HU_D04 关节重映射（腿/腰直接复制，头部填零，腕部 roll↔yaw 交换）
- [x] 2.2 集成 MuJoCo FK：加载 HU_D04 模型，逐帧设置重映射后的 qpos，调用 `mj_forward` 计算 body_pos_w/quat/vel
- [x] 2.3 从 MuJoCo 模型自动提取 body_names 和 joint_names 写入输出 NPZ
- [x] 2.4 运行转换：输入 `climb_14_z_scale_1.0.npz`，输出 `data/motions/hu_d04_31dof/whole_body_tracking/climb_14_holosoma.npz`
- [x] 2.5 验证输出 NPZ 包含所有必需 key（fps, joint_names, body_names, joint_pos, joint_vel, body_pos_w, body_quat_w, body_lin_vel_w, body_ang_vel_w）

## 3. 机器人配置注册

- [x] 3.1 从 `HU_D04_01_gmr.xml` 提取 31 个关节名和 body 名列表
- [x] 3.2 从 `HU_D04_01.urdf` 提取关节限位（position lower/upper, velocity, effort）
- [x] 3.3 从 `HU_D04_01.srdf` 推算 PD 增益（stiffness/damping），按关节组分组
- [x] 3.4 定义对称映射 `symmetry_joint_names`（left↔right 关节对）和 `flip_sign_joint_names`
- [x] 3.5 在 `config_values/robot.py` 的 `DEFAULTS` 中注册 `hu_d04_31dof` RobotConfig

## 4. WBT 实验配置

- [x] 4.1 创建 `config_values/wbt/hu_d04/` 目录结构（__init__.py, experiment.py, command.py, reward.py, observation.py, termination.py, randomization.py）
- [x] 4.2 实现 observation 配置：actor obs（motion_command + ref_ori + ang_vel + dof_pos31 + dof_vel31 + actions31），critic obs 额外加 pos/ori/lin_vel
- [x] 4.3 实现 action 配置：`JointPositionActionTerm`，31 维动作空间
- [x] 4.4 实现 reward 配置：tracking rewards + regularization，body_names_to_track 使用 HU_D04 body 名
- [x] 4.5 实现 termination 配置：timeout + BadTrackingZOnly
- [x] 4.6 实现 command 配置：MotionCommand 引用转换后的 HU_D04 NPZ
- [x] 4.7 实现 randomization 配置：push/actuator/material/COM/action_delay
- [x] 4.8 实现 curriculum 配置：AverageEpisodeLengthTracker
- [x] 4.9 创建 experiment.py，组合所有配置为 `hu_d04_31dof_wbt_fast_sac` 预设
- [x] 4.10 在 `config_values/experiment.py` 注册实验预设

## 5. 测试验证

- [x] 5.1 小规模训练测试：`num_envs=100, headless=True`，验证环境初始化无报错
- [ ] 5.2 检查训练日志：reward 是否正常下降，是否出现 NaN/Inf
- [ ] 5.3 调整 PD 增益（如出现振荡或跟踪失败）
