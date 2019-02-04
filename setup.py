import os
from setuptools import setup, find_packages

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# TODO use setuptools utils
install_requires = open(
    os.path.join(
        BASE_DIR,
        'requirements.txt'
    ),
    'r'
).read().splitlines()

test_requires = []

setup_requires = install_requires + []

setup(
    name='yaost',
    version='0.1',
    packages=find_packages(exclude=['tests']),
    install_requires=install_requires,
    tests_require=test_requires,
    setup_requires=setup_requires,
    include_package_data=True,
)
