"""Tests for URDF structure validation.

These tests verify that URDF files have correct structure for physics simulation.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
URDF_PATH = PROJECT_ROOT / "src/holosoma/holosoma/data/motions/g1_29dof/whole_body_tracking/climb_14_assets/multi_boxes_z_scale_1.0.urdf"


def parse_urdf(urdf_path: Path) -> ET.Element:
    """Parse URDF file and return root element."""
    tree = ET.parse(urdf_path)
    return tree.getroot()


def get_link_names(root: ET.Element) -> list[str]:
    """Get all link names from URDF."""
    return [link.get("name") for link in root.findall("link")]


def get_joint_info(root: ET.Element) -> list[dict]:
    """Get all joint information from URDF."""
    joints = []
    for joint in root.findall("joint"):
        joints.append({
            "name": joint.get("name"),
            "type": joint.get("type"),
            "parent": joint.find("parent").get("link") if joint.find("parent") is not None else None,
            "child": joint.find("child").get("link") if joint.find("child") is not None else None,
        })
    return joints


class TestURDFStructure:
    """Test URDF file structure for fixed base simulation."""

    def test_urdf_file_exists(self):
        """URDF file should exist."""
        assert URDF_PATH.exists(), f"URDF file not found: {URDF_PATH}"

    def test_has_single_link(self):
        """URDF should have exactly one link for RigidObject compatibility."""
        root = parse_urdf(URDF_PATH)
        link_names = get_link_names(root)
        assert len(link_names) == 1, f"Expected 1 link, got {len(link_names)}: {link_names}"

    def test_link_is_not_base_link(self):
        """Link should not be named base_link to avoid conflicts."""
        root = parse_urdf(URDF_PATH)
        link_names = get_link_names(root)
        assert "base_link" not in link_names, "base_link should be renamed to avoid conflicts"

    def test_link_name_is_multi_boxes(self):
        """Link should be named multi_boxes_link for clarity."""
        root = parse_urdf(URDF_PATH)
        link_names = get_link_names(root)
        assert "multi_boxes_link" in link_names, f"Expected multi_boxes_link, got: {link_names}"

    def test_has_no_joints(self):
        """URDF should have no joints when using fix_base=true."""
        root = parse_urdf(URDF_PATH)
        joints = get_joint_info(root)
        assert len(joints) == 0, f"Expected no joints, got {len(joints)}: {joints}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
