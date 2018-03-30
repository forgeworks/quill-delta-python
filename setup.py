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
    install_requires=['diff-match-patch', 'lxml', 'cssutils'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/forgeworks/delta-py/issues',
        'Source': 'https://github.com/forgeworks/delta-py',
    },
    classifiers=[
        'Development Status :: 5 - Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Text Processing :: Markup'
    ],

)
