#!/usr/bin/env python

from setuptools import setup, find_packages

# The actual setup function call
setup(
    name='FLiBe-TC',
    version='0.0.1',
    author='Ondrej Chvala',
    description='',
    package_dir={
        '': '.',
        # ...
    },
    # Alternatively can be auto-generated with setuptools.find_packages ...
    packages=find_packages(),
    # https://packaging.python.org/en/latest/discussions/install-requires-vs-requirements/
    install_requires=[
        'numpy',
        'json5',
        'pytest',
        'pytest-subtests',
        'setuptools',
        'matplotlib',
        'scipy',
    ]
)
