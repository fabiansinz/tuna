#!/usr/bin/env python
from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='tuna',
    version='0.0.0',
    description='Library to evaluate tuning of neurons',
    author='Fabian Sinz, Alex Ecker, Dimitri Yatsenko',
    packages=find_packages(exclude=[]),
    install_requires=['numpy', 'scipy'],
)
