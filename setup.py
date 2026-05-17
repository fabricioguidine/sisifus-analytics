"""Compatibility shim - project metadata lives in pyproject.toml.

This file is kept so that ``pip install -e .`` works with legacy toolchains.
Modern PEP 517 / PEP 621 builds read everything from pyproject.toml.
"""

from setuptools import setup

setup()
