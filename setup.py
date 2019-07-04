"""RAK811 library and command line utility.

Setup file for the project

Copyright 2019 Philippe Vanhaesendonck

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

SPDX-License-Identifier: Apache-2.0
"""

from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='rak811',
    version='0.7.0',
    description='Interface for RAK811 LoRa module',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/AmedeeBulle/pyrak811',
    author='Philippe Vanhaesendonck',
    author_email='philippe.vanhaesendonck@e-bulles.be',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Operating System :: POSIX :: Linux',
    ],
    packages=find_packages(),
    python_requires='>=3.5',
    install_requires=[
        'click>=7.0',
        'pyserial',
        'RPi.GPIO; platform_machine=="armv7l" or platform_machine=="armv6l"'
    ],
    extras_require={
        'test': [
            'flake8',
            'flake8-comprehensions',
            'flake8-docstrings',
            'flake8-import-order',
            'pep8-naming==0.5.0',
            'pytest',
            'mock',
            'coverage',
            'tox',
        ],
    },
    entry_points={
        'console_scripts': [
            'rak811=rak811.cli:cli',
        ],
    },

)
