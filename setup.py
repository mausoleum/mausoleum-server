#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='MausoleumServer',
      version='0.1',
      description='Server for file sharing with potentially untrusted clients/servers',
      author='Alex Chernyakhovsky, Drew Dennison, and Patrick Hurst',
      author_email='mausoleum@mit.edu',
      url='https://github.com/mausoleum/mausoleum-server',
      packages=find_packages(),
     )
