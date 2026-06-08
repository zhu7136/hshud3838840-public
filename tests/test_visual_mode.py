"""Tests for visual mode in training script.

These tests verify that the --visual parameter works correctly.
"""

import subprocess
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "train_climb_14.sh"


class TestVisualMode:
    """Test visual mode parameter."""

    def test_visual_flag_accepted(self):
        """Script should accept --visual flag."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "--visual", "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_visual_flag_in_help(self):
        """Help should mention --visual flag."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert "--visual" in result.stdout
        assert "Enable visualization" in result.stdout

    def test_visual_config_displayed(self):
        """Configuration should show headless=False when --visual is used."""
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "--visual", "--num_envs", "2"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=30,
        )
        # Should show headless=False in configuration
        assert "headless:     False (visualization)" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
