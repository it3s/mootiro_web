#!/usr/bin/env python
# -*- coding: utf-8 -*-

# http://peak.telecommunity.com/DevCenter/setuptools#developer-s-guide
# from distutils.core import setup
from setuptools import setup, find_packages

setup(
    name = "mootiro_web",
    version = '0.2.0a1',
    url = 'https://github.com/it3s/mootiro_web',
    download_url = "https://github.com/it3s/mootiro_web/downloads",
    author = 'The IT3S team',
    license = 'BSD',
    packages = find_packages(),
    package_data = {'': ['*.txt', '*.js']},
    author_email = "team@it3s.org",
    description = "Library for web development, containing javascript i18n " \
                  "and stuff for the Pyramid web framework.",
    entry_points = '''
[babel.extractors]
jquery_templates = mootiro_web.transecma:extract_jquery_templates

[console_scripts]
po2json = mootiro_web.transecma:po2json_command
''',
    zip_safe = False,
    test_suite='mootiro_web',
    keywords = ["python", 'HTML', 'Pyramid', 'web', 'javascript', 'i18n'],
    classifiers = [ # http://pypi.python.org/pypi?:action=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        'License :: OSI Approved :: BSD License',
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
        'Topic :: Text Processing :: General',
    ],
    long_description = '''Library developed for http://mootiro.org,
including a couple of modules for the Pyramid web framework:
a Genshi connector and a Kajiki connector.''',
)
