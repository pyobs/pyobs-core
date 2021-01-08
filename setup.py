#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name='pyobs-core',
    version='0.11',
    description='robotic telescope software',
    author='Tim-Oliver Husser',
    author_email='thusser@uni-goettingen.de',
    packages=find_packages(include=['pyobs', 'pyobs.*']),
    entry_points={
        'console_scripts': [
            'pyobs=pyobs.cli.pyobs:main',
            'pyobsd=pyobs.cli.pyobsd:main',
        ],
        'gui_scripts': [
            'pyobsw=pyobs.cli.pyobsw:main',
        ]
    },
    python_requires='>=3.7',
    install_requires=[
        'scipy',
        'paramiko',
        'pandas',
        'pytz',
        'astropy',
        'astroplan',
        'PyYAML',
        'numpy',
        'sleekxmpp',
        'py_expression_eval',
        'requests'
    ],
    extras_require={
        'full':  [
            'photutils',
            'lmfit',
            'tornado',
            'sep;platform_system=="Linux"',
            'pyinotify;platform_system=="Linux"',
            'python-daemon;platform_system=="Linux"'
        ]
    }
)
