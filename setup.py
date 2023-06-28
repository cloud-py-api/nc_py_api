#!/usr/bin/env python
"""Script to build wheel"""
from setuptools import setup


def get_version():
    version_file = "nc_py_api/_version.py"
    with open(version_file, encoding="utf-8") as f:
        exec(compile(f.read(), version_file, "exec"))  # pylint: disable=exec-used
    return locals()["__version__"]


setup(version=get_version())
