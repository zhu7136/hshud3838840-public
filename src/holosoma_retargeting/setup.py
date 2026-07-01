from setuptools import find_packages, setup  # type: ignore[import-untyped]

setup(
    name="holosoma-retargeting",
    version="0.1.0",
    description="holosoma-retargeting: retargeting components for converting human motions to robot motions",
    author="Amazon FAR Team",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        # Allow numpy 1.26.x (for isaacsim/isaaclab envs) up to <2.4.
        # reason: numpy 2.4+ triggers "TypeError: only 0-dimensional arrays can
        # be converted to Python scalars" in yourdf/urdf.py::1078 when
        # converting float(q). numpy 1.26.x and 2.0-2.3 are unaffected.
        "numpy>=1.26,<2.4",
        "torch",
        "tqdm",
        "scipy",
        "matplotlib",
        "trimesh",
        "smplx",
        "jinja2",
        "mujoco",
        "viser",
        "robot_descriptions",
        "yourdfpy",
        "cvxpy",
        "libigl",
        "tyro",
    ],
)
