#!/usr/bin/env python3

from setuptools import setup
from setuptools import find_packages

requirements = map(str.strip, open('requirements.txt').readlines())
dev_requirements = map(str.strip, open('requirements-dev.txt').readlines())

setup(
    name='KicadModTree',
    version='1.0',
    author='Thomas Pointhuber',
    author_email='thomas.pointhuber@gmx.at',
    url='https://github.com/pointhi/kicad-footprint-generator',
    description="creating kicad footprints using python scripts",
    long_description="""
        This is a standalone implementation of the KiCad footprint format as well as helper functions to simplify the
        creation of custom footprints. It is heavily used in the official footprint library.
        """,
    license="GPL3+",

    install_requires=requirements,
    extras_require={
        'test': dev_requirements
    },
    packages=find_packages('.', exclude=["*tests*", "*examples*"]),
    test_suite='tests',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)'
    ],
)