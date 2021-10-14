# -*- mode: python; coding: utf-8 -*-
# Copyright 2019-2021 the .NET Foundation
# Licensed under the MIT License

import os
from setuptools import setup, Extension

def get_long_desc():
    in_preamble = True
    lines = []

    with open('README.md', 'rt', encoding='utf8') as f:
        for line in f:
            if in_preamble:
                if line.startswith('<!--pypi-begin-->'):
                    in_preamble = False
            else:
                if line.startswith('<!--pypi-end-->'):
                    break
                else:
                    lines.append(line)

    lines.append('''

For more information, including installation instructions, please visit [the
project homepage].

[the project homepage]: https://github.com/WorldWideTelescope/wwt_kernel_data_relay/
''')
    return ''.join(lines)


setup_args = dict(
    name = 'wwt_kernel_data_relay',  # cranko project-name
    version = '0.1.0',  # cranko project-version
    description = 'Jupyter server extension to allow kernels to make data web-accessible',
    long_description = get_long_desc(),
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/WorldWideTelescope/wwt_kernel_data_relay/',
    license = 'MIT',
    platforms = 'Linux, Mac OS X, Windows',

    author = 'AAS WorldWide Telescope Team',
    author_email = 'wwt@aas.org',

    classifiers = [
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: Visualization',
    ],

    packages = [
        'wwt_kernel_data_relay',
        #'wwt_kernel_data_relay.tests',
    ],
    include_package_data = True,

    install_requires = [
        'jupyter-client>=7',
        'notebook>=6',
        'tornado>=6',
        'traitlets>=5',
    ],

    extras_require = {
        'test': [
            'pytest-cov',
        ],
        'docs': [
            'astropy-sphinx-theme',
            'numpydoc',
            'sphinx',
            'sphinx-automodapi',
        ],
    },
)

if __name__ == '__main__':
    setup(**setup_args)
