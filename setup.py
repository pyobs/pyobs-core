#!/usr/bin/env python3
from setuptools import setup, find_packages
from pyobs.version import VERSION

setup(
    name='pyobs',
    version=VERSION,
    description='robotic telescope software',
    author='Tim-Oliver Husser',
    author_email='thusser@uni-goettingen.de',
    packages=find_packages(include=['pyobs', 'pyobs.*']),
    scripts=['bin/pyobs', 'bin/pyobsd']
)
