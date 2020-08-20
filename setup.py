import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class PyTest(TestCommand):
    # user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


# TODO use setuptools utils
install_requires = open(
    os.path.join(
        BASE_DIR,
        'requirements.txt'
    ),
    'r'
).read().splitlines()

with open(os.path.join(BASE_DIR, 'README.md'), 'r') as fh:
    long_description = fh.read()

test_requires = ['pytest']

setup_requires = install_requires + []

setup(
    name='yaost',
    version='0.2.1',
    author='Andrey Proskurnev',
    author_email='andrey@proskurnev.ru',
    packages=find_packages(exclude=['tests']),
    install_requires=install_requires,
    tests_require=test_requires,
    cmdclass={'test': PyTest},
    setup_requires=setup_requires,
    description='Yet another python to openscad translator',
    long_description=long_description,
    long_description_content_type='text/markdown',
    include_package_data=True,
    url='https://github.com/ariloulaleelay/yaost',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
