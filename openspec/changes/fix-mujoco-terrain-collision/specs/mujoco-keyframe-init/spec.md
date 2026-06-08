## ADDED Requirements

### Requirement: 设置 MuJoCo keyframe 确保 reset 正确
系统 SHALL 在 `prepare_sim()` 中设置 MuJoCo keyframe，使 viewer reset 按钮恢复到配置的 init_state.pos。

#### Scenario: keyframe 包含正确的初始位置
- **WHEN** `prepare_sim()` 完成
- **THEN** MuJoCo model 中存在一个 keyframe，其 qpos 包含 init_state.pos 的位置

#### Scenario: viewer reset 恢复到 init_state.pos
- **WHEN** 用户在 MuJoCo viewer 中点击 simulation reset
- **THEN** 机器人位置恢复到 init_state.pos（而非原点 [0,0,0]）
