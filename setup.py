import os

from setuptools import setup
from setuptools import find_packages

here = os.path.join(os.path.dirname(__file__))


__version__ = None
with open(os.path.join(here, 'optimizely', 'version.py')) as _file:
  exec(_file.read())

with open(os.path.join(here, 'requirements', 'core.txt')) as _file:
  REQUIREMENTS = _file.read().splitlines()

with open(os.path.join(here, 'requirements', 'test.txt')) as _file:
  TEST_REQUIREMENTS = _file.read().splitlines()
  TEST_REQUIREMENTS = list(set(REQUIREMENTS + TEST_REQUIREMENTS))

setup(
    name='optimizely-sdk',
    version=__version__,
    description="SDK for Optimizely's Full Stack Python project.",
    author='Optimizely',
    author_email='developers@optimizely.com',
    url='https://github.com/optimizely/python-sdk',
    license=open('LICENSE').read(),
    classifiers=[
      'Development Status :: 5 - Production/Stable',
      'Environment :: Web Environment',
      'Intended Audience :: Developers',
      'Operating System :: OS Independent',
      'Programming Language :: Python',
      'Programming Language :: Python :: 2.7',
      'Programming Language :: Python :: 3.4',
      'Programming Language :: Python :: 3.5',
      'Programming Language :: Python :: 3.6'
    ],
    packages=find_packages(
      exclude=['tests']
    ),
    install_requires=REQUIREMENTS,
    tests_require=TEST_REQUIREMENTS,
    test_suite='tests'
)
