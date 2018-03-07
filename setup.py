#!/usr/bin/env python

from setuptools import setup

setup(
    name='quill-delta',
    version='1.0',
    description='Python port of the Quill-JS Delta library',
    author='Brantley Harris',
    author_email='brantley@forge.works',
    packages=['delta'],
    license="MIT License",
    install_requires=['cssutils', 'diff-match-patch', 'lxml'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'mock'],   
)
