#!/usr/bin/env python

from setuptools import setup


setup(name='PyPipeline',
      version='0.1',
      description='Python Real-time Line Viewer',

      author='Stephen Soltesz',
      author_email='stephen-soltesz@users.github.com',
      url='http://github.com/stephen-soltesz/pipeline/',
      license='Apache License Version 2',

      install_requires=[
        'python-gflags >= 1.0',
        'matplotlib >= 1.3',
        'mock >= 1.0',
      ],
      packages=['src/pipeline'],
      scripts=['src/lineview.py','src/lineprobe.py'],
      data_files=[('LICENSE', ['LICENSE']),
                  ('README.md', ['README.md'])],

      test_suite='tests',
)
