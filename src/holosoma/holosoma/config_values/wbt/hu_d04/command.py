"""Whole Body Tracking command presets for the HU_D04 robot."""

from holosoma.config_types.command import CommandManagerCfg, CommandTermCfg, MotionConfig, NoiseToInitialPoseConfig

init_pose_config = NoiseToInitialPoseConfig(
    overall_noise_scale=1.0,
    dof_pos=0.1,
    root_pos=[0.05, 0.05, 0.01],
    root_rot=[0.1, 0.1, 0.2],
    root_lin_vel=[0.5, 0.5, 0.2],
    root_ang_vel=[0.52, 0.52, 0.78],
    object_pos=[0.05, 0.05, 0.0],
)

body_names_to_track = [
    "base_link",
    "left_hip_roll_link",
    "left_knee_link",
    "left_ankle_roll_link",
    "right_hip_roll_link",
    "right_knee_link",
    "right_ankle_roll_link",
    "waist_pitch_link",
    "left_shoulder_roll_link",
    "left_elbow_link",
    "left_wrist_roll_link",
    "right_shoulder_roll_link",
    "right_elbow_link",
    "right_wrist_roll_link",
]

motion_config = MotionConfig(
    motion_file="holosoma/data/motions/hu_d04_31dof/whole_body_tracking/climb_14_holosoma.npz",
    body_names_to_track=body_names_to_track,
    body_name_ref=["waist_pitch_link"],
    use_adaptive_timesteps_sampler=True,
    noise_to_initial_pose=init_pose_config,
)

motion_config_29dof = MotionConfig(
    motion_file="holosoma/data/motions/hu_d04_29dof/whole_body_tracking/climb_14_holosoma.npz",
    body_names_to_track=body_names_to_track,
    body_name_ref=["waist_pitch_link"],
    use_adaptive_timesteps_sampler=True,
    noise_to_initial_pose=init_pose_config,
)

hu_d04_31dof_wbt_command = CommandManagerCfg(
    params={},
    setup_terms={
        "motion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.wbt:MotionCommand",
            params={
                "motion_config": motion_config,
            },
        ),
    },
    reset_terms={
        "motion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.wbt:MotionCommand",
        )
    },
    step_terms={
        "motion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.wbt:MotionCommand",
        )
    },
)

hu_d04_29dof_wbt_command = CommandManagerCfg(
    params={},
    setup_terms={
        "motion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.wbt:MotionCommand",
            params={
                "motion_config": motion_config_29dof,
            },
        ),
    },
    reset_terms={
        "motion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.wbt:MotionCommand",
        )
    },
    step_terms={
        "motion_command": CommandTermCfg(
            func="holosoma.managers.command.terms.wbt:MotionCommand",
        )
    },
)

__all__ = ["hu_d04_31dof_wbt_command", "hu_d04_29dof_wbt_command"]
