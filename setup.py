#!/usr/bin/env python3

# std
from distutils.core import setup

# noinspection PyUnresolvedReferences
import setuptools  # see below (1)
from pathlib import Path

# (1) see https://stackoverflow.com/questions/8295644/
# Without this import, install_requires won't work.

description = ""

this_dir = Path(__file__).resolve().parent

packages = setuptools.find_packages()

with (this_dir / "README.md").open() as fh:
    long_description = fh.read()

with (this_dir / "requirements.txt").open() as rf:
    requirements = [
        req.strip()
        for req in rf.readlines()
        if req.strip() and not req.startswith("#")
    ]


setup(
    name="sksurvey",
    packages=packages,
    install_requires=requirements,
    url="",
    project_urls={"Bug Tracker": None, "Source Code": None,},
    include_package_data=True,
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
)
