"""Whole Body Tracking experiment presets for the HU_D04 robot."""

from dataclasses import replace

from holosoma.config_types.experiment import ExperimentConfig, TrainingConfig
from holosoma.config_values import (
    algo,
    command,
    curriculum,
    observation,
    randomization,
    reward,
    robot,
    simulator,
    terrain,
)
from holosoma.config_values.wbt.hu_d04 import (
    action,
    command as hu_d04_command,
    curriculum as hu_d04_curriculum,
    observation as hu_d04_observation,
    randomization as hu_d04_randomization,
    reward as hu_d04_reward,
    termination as hu_d04_termination,
)

hu_d04_31dof_wbt_fast_sac = ExperimentConfig(
    training=TrainingConfig(
        project="WholeBodyTracking",
        name="hu_d04_31dof_wbt_fast_sac_manager",
        num_envs=4096,
    ),
    env_class="holosoma.envs.wbt.wbt_manager.WholeBodyTrackingManager",
    algo=replace(
        algo.fast_sac,
        config=replace(
            algo.fast_sac.config,
            num_learning_iterations=400000,
            v_max=20.0,
            v_min=-20.0,
            gamma=0.99,
            num_steps=1,
            num_updates=4,
            num_atoms=501,
            policy_frequency=2,
            target_entropy_ratio=0.5,
            tau=0.05,
            use_symmetry=False,
        ),
    ),
    simulator=replace(
        simulator.isaacsim,
        config=replace(
            simulator.isaacsim.config,
            sim=replace(
                simulator.isaacsim.config.sim,
                max_episode_length_s=10.0,
            ),
        ),
    ),
    robot=replace(
        robot.hu_d04_31dof,
        control=replace(
            robot.hu_d04_31dof.control,
            action_scale=0.25,
            action_scales_by_effort_limit_over_p_gain=True,
        ),
        asset=replace(robot.hu_d04_31dof.asset, enable_self_collisions=True),
        init_state=replace(robot.hu_d04_31dof.init_state, pos=[0.0, 0.0, 1.0]),
    ),
    terrain=terrain.terrain_locomotion_plane,
    observation=hu_d04_observation.hu_d04_31dof_wbt_observation,
    action=action.hu_d04_31dof_joint_pos,
    termination=hu_d04_termination.hu_d04_31dof_wbt_termination,
    randomization=hu_d04_randomization.hu_d04_31dof_wbt_randomization,
    command=hu_d04_command.hu_d04_31dof_wbt_command,
    curriculum=hu_d04_curriculum.hu_d04_31dof_wbt_curriculum,
    reward=hu_d04_reward.hu_d04_31dof_wbt_reward,
)

hu_d04_29dof_wbt_fast_sac = replace(
    hu_d04_31dof_wbt_fast_sac,
    training=replace(
        hu_d04_31dof_wbt_fast_sac.training,
        name="hu_d04_29dof_wbt_fast_sac_manager",
    ),
    robot=replace(
        robot.hu_d04_29dof,
        control=replace(
            robot.hu_d04_29dof.control,
            action_scale=0.25,
            action_scales_by_effort_limit_over_p_gain=True,
        ),
        asset=replace(robot.hu_d04_29dof.asset, enable_self_collisions=True),
        init_state=replace(robot.hu_d04_29dof.init_state, pos=[0.0, 0.0, 0.93]),
    ),
    observation=hu_d04_observation.hu_d04_29dof_wbt_observation,
    action=action.hu_d04_29dof_joint_pos,
    termination=hu_d04_termination.hu_d04_29dof_wbt_termination,
    randomization=hu_d04_randomization.hu_d04_29dof_wbt_randomization,
    command=hu_d04_command.hu_d04_29dof_wbt_command,
    curriculum=hu_d04_curriculum.hu_d04_29dof_wbt_curriculum,
    reward=hu_d04_reward.hu_d04_29dof_wbt_reward,
)

__all__ = ["hu_d04_31dof_wbt_fast_sac", "hu_d04_29dof_wbt_fast_sac"]
