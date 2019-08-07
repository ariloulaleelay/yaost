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

with open(os.path.join(BASE_DIR, 'README.md'), 'r') as fh:
    long_description = fh.read()

test_requires = []

setup_requires = install_requires + []

setup(
    name='yaost',
    version='0.1.3',
    author='Andrey Proskurnev',
    author_email='andrey@proskurnev.ru',
    packages=find_packages(exclude=['tests']),
    install_requires=install_requires,
    tests_require=test_requires,
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
