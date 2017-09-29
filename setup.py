#!/usr/bin/env python
from setuptools import setup, find_packages
import os


data_files = [(d, [os.path.join(d, f) for f in files])
              for d, folders, files in os.walk(os.path.join('src', 'config'))]

setup(name='rule-chains',
      version='1.0',
      description='chain together rules from grok',
      author='adam pridgen',
      author_email='dso@thecoverofnight.com',
      install_requires=['toml'],
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      package_data={
           'rule_chains': ['config/*', 'patterns/*'],
      },
      data_files=data_files,
)
