#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name='pyobs-core',
    version='0.7',
    description='robotic telescope software',
    author='Tim-Oliver Husser',
    author_email='thusser@uni-goettingen.de',
    packages=find_packages(include=['pyobs', 'pyobs.*']),
    scripts=[
        'bin/pyobs',
        'bin/pyobsd'
    ],
    install_requires=[
        'sep',
        'photutils',
        'scipy',
        'pyinotify',
        'paramiko',
        'pandas',
        'matplotlib',
        'pytz',
        'astropy',
        'astroplan',
        'Pillow',
        'PyYAML',
        'numpy',
        'lmfit',
        'aplpy',
        'tornado',
        'sleekxmpp',
        'py_expression_eval',
        'colour',
        'requests',
        'python-daemon;platform_system=="Linux"'
    ]
)
