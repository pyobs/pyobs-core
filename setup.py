#!/usr/bin/env python3
from setuptools import setup, find_packages
from pytel.version import VERSION

setup(
    name='pytel',
    version=VERSION,
    description='robotic telescope software',
    author='Tim-Oliver Husser',
    author_email='thusser@uni-goettingen.de',
    packages=find_packages(include=['pytel', 'pytel.*']),
    scripts=['bin/pytel', 'bin/pyteld']
)
