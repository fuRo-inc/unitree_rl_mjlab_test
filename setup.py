"""Installation script for the 'unitree_rl_mjlab' python package."""

from setuptools import setup, find_packages

INSTALL_REQUIRES = [
    "mjlab>=1.3.0,<2",
]

setup(
    name="unitree_rl_mjlab",
    version="0.0.1",
    packages=find_packages(
        include=[
            "src",
            "src.*",
            "furo_rl_locomotion_mjlab",
            "furo_rl_locomotion_mjlab.*",
        ]
    ),
    install_requires=INSTALL_REQUIRES,
    python_requires=">=3.10,<3.14",
)
