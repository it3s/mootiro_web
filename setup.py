#!/usr/bin/env python
# -*- coding: utf-8 -*-
# http://docs.python.org/whatsnew/pep-328.html
from __future__ import absolute_import
from __future__ import print_function   # deletes the print statement
from __future__ import unicode_literals # unicode by default

# from distutils.core import setup

# http://peak.telecommunity.com/DevCenter/setuptools#developer-s-guide

from setuptools import setup, find_packages

setup(
    url = 'http://mootiro.org',
    name = "mootiro_web",
    author = 'the IT3S team',
    version = '0.1.0',
    license = 'BSD',
    packages = find_packages(),
    author_email = "team@it3s.org",
    download_url = "https://github.com/it3s/mootiro_web",
    description = "A library for many purposes",
    entry_points = '''
[babel.extractors]
jquery_templates = mootiro_web.transecma:extract_jquery_templates

[console_scripts]
po2json = mootiro_web.transecma:po2json_command
''',
    zip_safe = False,
    keywords = ["python", 'HTML', 'Pyramid', 'web'],
    classifiers = [ # http://pypi.python.org/pypi?:action=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        'License :: OSI Approved :: BSD License',
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
        'Topic :: Text Processing :: General',
    ],
    long_description = '''Library developed for http://mootiro.org,
including a couple of modules for the Pyramid web framework:
a Genshi connector and a Kajiki connector.''',
)
