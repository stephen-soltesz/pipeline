#!/usr/bin/env python

from setuptools import setup


setup(name='PyPipeline',
      version='0.1',
      description='Python Real-time Line Viewer',

      author='Stephen Soltesz',
      url='http://github.com/stephen-soltesz/pipeline/',
      license='Apache License Version 2',

      install_requires=[
        'gflags >= 1.0',
        'matplotlib >= 1.3',
        'mock >= 1.0',
      ],
      scripts=['src/lineview.py','src/lineprobe.py'],
      data_files=[('LICENSE', ['LICENSE']),
                  ('README.md', ['README.md'])],

      test_suite='tests',
)
