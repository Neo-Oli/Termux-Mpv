#!/usr/bin/env python3
# coding=utf-8
from __future__ import unicode_literals, print_function
import sys
from termuxmpv import __version__
from setuptools import setup
import os


def read_reqs(path):
    with open(path, 'r') as file:
            return list(file.readlines())
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
# requires = read_reqs('requirements.txt')
setup(
    name='Termux-Mpv',
    version=__version__,
    description='Wrapper for Mpv to display notification in Android/Termux',
    author='Oliver Schmidhauser',
    author_email='oli@glow.li',
        url='oliverse.ch',
    # long_description=(
        # "Virtual pet simulator"
    # ),
    packages=[str('termuxmpv')],
        # data_files=[('translations', ['translations/en.yml','translations/de.yml']),
                             # ('config',['config/default.yml'])],
    license='',
    platforms='Linux x86, x86-64',
    # install_requires=requires,
    entry_points={'console_scripts': ['termuxmpv = termuxmpv.__main__:main']},
)
