"""Locomotion action presets for the HU_D04 robot."""

from holosoma.config_types.action import ActionManagerCfg, ActionTermCfg

hu_d04_29dof_joint_pos = ActionManagerCfg(
    terms={
        "joint_control": ActionTermCfg(
            func="holosoma.managers.action.terms.joint_control:JointPositionActionTerm",
            params={},
            scale=1.0,
            clip=None,
        ),
    }
)

__all__ = ["hu_d04_29dof_joint_pos"]
