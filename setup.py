#
# Copyright 2015-2017 (c) Andrey Galkin
#


from setuptools import setup, find_packages
    
import os, sys

project_path = os.path.dirname( __file__ )
sys.path.insert( 0, project_path )
from futoin.cid import __version__ as version

with open(os.path.join(project_path, 'README.rst'), 'r') as f:
    long_description = f.read()

config = {
    'name': 'futoin-cid',
    'version': version,
    'namespace_packages': ['futoin'],

    'description': 'FutoIn Continuous Integration & Delivery Tool',
    'long_description': long_description,

    'author': 'Andrey Galkin',
    'author_email': 'andrey@futoin.org',

    'url': 'https://github.com/futoin/cid-tool',
    'download_url': 'https://github.com/futoin/cid-tool/archive/master.zip',

    'install_requires': [
        'docopt',
        #'requests>=2.18.4',
        # be compatible with docker/docker-compose
        'requests(>=2.5.2,!=2.12.2,!=2.11.0,!=2.18.0)',
        'urllib3>=1.21.1',
    ],
    # temporary disabled due to py3 failures on setup of pylint
    #'setup_requires': ['autopep8', 'pylint'],
    'extras_require': {
        'test': ['nose'],
    },
    'python_requires': '>=2.7',
    'packages': find_packages(exclude=['bind', 'tests']),
    
    'entry_points': {
        'console_scripts': [
            'cid=futoin.cid.cli:run',
            'futoin-cid=futoin.cid.cli:run',
        ],
    },
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Installation/Setup',
        'Programming Language :: C',
        'Programming Language :: C++',
        'Programming Language :: Java',
        'Programming Language :: JavaScript',
        'Programming Language :: Other',
        'Programming Language :: PHP',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Ruby',
        'Programming Language :: Unix Shell',
        'Environment :: Console',
    ],
    'keywords': 'php ruby node nodejs npm gem rvm nvm grunt gulp bower \
 puppet build deploy futoin cmake make gradle maven java composer bundler',
    'license': 'Apache 2.0',
}

setup(**config)
