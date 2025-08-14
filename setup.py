"""asf_levies_model."""

from pathlib import Path
from setuptools import find_packages
from setuptools import setup


def read_lines(path):
    """Read lines of `path`."""
    with open(path) as f:
        return f.read().splitlines()


BASE_DIR = Path(__file__).parent


setup(
    name="asf_levies_model",
    long_description=open(BASE_DIR / "README.md").read(),
    install_requires=[
        "pandas",
        "numpy",
        "scipy",
        "matplotlib",
        "requests",
        "PyYAML",
        "pandera",
        "python-dateutil",
        "python-calamine",
    ],
    packages=find_packages(exclude=["docs"]),
    version="0.1.0",
    description="Analytical model of domestic energy bills and levies.",
    author="Nesta",
    license="MIT",
    package_data={
        "": [
            "base.yaml",
            "master_archetypes_data.pkl",
        ]
    },
    include_package_data=True,
)
