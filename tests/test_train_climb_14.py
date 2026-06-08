"""Tests for train_climb_14.sh script."""

import subprocess
import pytest
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "train_climb_14.sh"


def run_script(*args, check=True):
    """Helper to run the script and capture output."""
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    if check and result.returncode != 0:
        pytest.fail(f"Script failed: {result.stderr}")
    return result


class TestZScaleValidation:
    """Test z_scale parameter validation."""

    def test_valid_z_scales(self):
        """Script should accept valid z_scale values."""
        for z_scale in ["0.8", "0.9", "1.0", "1.1", "1.2"]:
            # We expect it to fail at environment check, not z_scale validation
            result = run_script("--z_scale", z_scale, check=False)
            assert "Invalid z_scale" not in result.stderr

    def test_invalid_z_scale(self):
        """Script should reject invalid z_scale values."""
        result = run_script("--z_scale", "1.5", check=False)
        assert result.returncode != 0
        assert "Invalid z_scale" in result.stderr

    def test_invalid_z_scale_negative(self):
        """Script should reject negative z_scale values."""
        result = run_script("--z_scale", "-1.0", check=False)
        assert result.returncode != 0
        assert "Invalid z_scale" in result.stderr


class TestHelpMessage:
    """Test help message display."""

    def test_help_flag(self):
        """Script should display help with --help flag."""
        result = run_script("--help", check=False)
        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "--z_scale" in result.stdout
        assert "--resume" in result.stdout
        assert "--status" in result.stdout


class TestStatusCommand:
    """Test --status command."""

    def test_status_no_runs(self):
        """Script should handle no training runs gracefully."""
        result = run_script("--status", check=False)
        # Should not crash, even if no runs exist
        assert result.returncode == 0


class TestPathResolution:
    """Test path resolution logic."""

    def test_script_exists(self):
        """Script file should exist."""
        assert SCRIPT_PATH.exists()

    def test_script_is_executable(self):
        """Script should be executable."""
        assert SCRIPT_PATH.stat().st_mode & 0o111


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
