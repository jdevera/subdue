#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os


def dump_sibling_file(file_name):
    with open(os.path.join(os.path.dirname(__file__), file_name), 'r') as f:
        return f.read()

setup(
    name = 'subdue',
    packages = ['subdue',
                'subdue.core',
                'subdue.core.color',
                ],
    version = '0.1.0',
    description = 'A framework to create commands with subcommands',
    author='Jacobo de Vera',
    author_email='devel@jacobodevera.com',
    url='https://www.github.com/jdevera/subdue',
    license='MIT',
    scripts=['scripts/subdue'],
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Topic :: Utilities'
        ],
    long_description=dump_sibling_file('README.rst'),
    test_suite='test'
    )
