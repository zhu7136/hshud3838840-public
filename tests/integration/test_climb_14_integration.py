"""Integration tests for climb_14 training pipeline.

These tests verify the training configuration and file structure
without actually starting training.
"""

import subprocess
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "train_climb_14.sh"


class TestConfigurationGeneration:
    """Test that correct configuration is generated."""

    def test_default_config_display(self):
        """Verify default configuration is displayed correctly."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "--z_scale", "1.0"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        # Should fail at environment check (no GPU), but config should be printed
        assert "z_scale:      1.0" in result.stdout
        assert "climb_14_mj_fps50.npz" in result.stdout
        assert "multi_boxes_z_scale_1.0.urdf" in result.stdout


class TestFileExistence:
    """Test that required files exist."""

    def test_motion_file_exists(self):
        """climb_14_mj_fps50.npz should exist."""
        motion_file = PROJECT_ROOT / "src/holosoma/holosoma/data/motions/g1_29dof/whole_body_tracking/climb_14_mj_fps50.npz"
        assert motion_file.exists(), f"Motion file not found: {motion_file}"

    def test_terrain_urdf_exists(self):
        """multi_boxes_z_scale_1.0.urdf should exist."""
        urdf = PROJECT_ROOT / "src/holosoma/holosoma/data/motions/g1_29dof/whole_body_tracking/climb_14_assets/multi_boxes_z_scale_1.0.urdf"
        assert urdf.exists(), f"Terrain URDF not found: {urdf}"

    def test_experiment_preset_exists(self):
        """g1_29dof_wbt_fast_sac_climb experiment should be defined."""
        exp_file = PROJECT_ROOT / "src/holosoma/holosoma/config_values/wbt/g1/experiment.py"
        content = exp_file.read_text()
        assert "g1_29dof_wbt_fast_sac_climb" in content


class TestScriptIntegration:
    """Test script integration with project structure."""

    def test_script_help(self):
        """Script should display help without errors."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_status_command(self):
        """Status command should work without errors."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "--status"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
