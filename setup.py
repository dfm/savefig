#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == "publish":
    os.system("python setup.py sdist upload")
    sys.exit(0)

# Handle encoding
major, minor1, minor2, release, serial = sys.version_info
if major >= 3:
    def rd(filename):
        f = open(filename, encoding="utf-8")
        r = f.read()
        f.close()
        return r
else:
    def rd(filename):
        f = open(filename)
        r = f.read()
        f.close()
        return r

setup(
    name="savefig",
    version="0.0.2",
    author="Daniel Foreman-Mackey",
    author_email="dan@dfm.io",
    py_modules=["savefig"],
    url="https://github.com/dfm/savefig",
    license="MIT",
    description="Save matplotlib figures with embedded metadata for "
                "reproducibility and profit",
    long_description=rd("README.rst"),
    package_data={"": ["README.rst", "LICENSE", "AUTHORS.rst"]},
    include_package_data=True,
    classifiers=[
        # "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
)
