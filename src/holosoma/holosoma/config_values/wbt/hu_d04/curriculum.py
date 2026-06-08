"""Whole Body Tracking curriculum presets for the HU_D04 robot."""

from holosoma.config_types.curriculum import CurriculumManagerCfg, CurriculumTermCfg

hu_d04_31dof_wbt_curriculum = CurriculumManagerCfg(
    params={
        "num_compute_average_epl": 1000,
    },
    setup_terms={
        "average_episode_tracker": CurriculumTermCfg(
            func="holosoma.managers.curriculum.terms.locomotion:AverageEpisodeLengthTracker",
            params={},
        ),
    },
    reset_terms={},
    step_terms={},
)

hu_d04_29dof_wbt_curriculum = hu_d04_31dof_wbt_curriculum

__all__ = ["hu_d04_31dof_wbt_curriculum", "hu_d04_29dof_wbt_curriculum"]
