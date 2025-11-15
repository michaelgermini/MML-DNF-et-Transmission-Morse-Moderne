#!/usr/bin/env python3
"""
Setup script for DNF-MML-Morse package
"""

from setuptools import setup, find_packages
import os

# Read the contents of README.md
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open('requirements.txt', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='dnf-mml-morse',
    version='1.0.0',
    description='Système de transmission de documents structurés via radio amateur',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Système DNF-MML-Morse',
    author_email='contact@dnf-mml-morse.org',
    url='https://github.com/dnf-mml-morse/dnf-mml-morse',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.0.0',
            'black>=22.0.0',
            'isort>=5.10.0',
            'mypy>=1.0.0',
            'flake8>=5.0.0',
            'sphinx>=5.0.0',
            'sphinx-rtd-theme>=1.2.0',
        ],
        'web': [
            'fastapi>=0.100.0',
            'uvicorn>=0.23.0',
            'websockets>=11.0.0',
        ],
        'radio': [
            'pyserial>=3.5',
            'sounddevice>=0.4.0',
            'numpy>=1.21.0',
        ],
        'ai': [
            'scikit-learn>=1.3.0',
            'tensorflow>=2.13.0',
            'transformers>=4.21.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'dnf-mml-morse=dnf_mml_morse.cli:main',
            'mml-convert=dnf_mml_morse.cli:mml_convert',
            'morse-transmit=dnf_mml_morse.cli:morse_transmit',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Communications :: Ham Radio',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Security :: Cryptography',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Topic :: Text Processing :: Markup',
    ],
    keywords='mml dnf morse radio transmission compression ham-radio',
    python_requires='>=3.8',
    project_urls={
        'Documentation': 'https://dnf-mml-morse.readthedocs.io/',
        'Source': 'https://github.com/dnf-mml-morse/dnf-mml-morse',
        'Tracker': 'https://github.com/dnf-mml-morse/dnf-mml-morse/issues',
        'Changelog': 'https://github.com/dnf-mml-morse/dnf-mml-morse/blob/main/CHANGELOG.md',
    },
)
