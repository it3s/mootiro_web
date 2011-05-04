#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals  # unicode by default

# http://babel.edgewall.org/wiki/Documentation/0.9/messages.html#writing-extraction-methods

def extract_jquery_templates(fileobj, keywords, comment_tags, options):
    """Extract messages from XXX files.
    :param fileobj: the file-like object the messages should be extracted
                    from
    :param keywords: a list of keywords (i.e. function names) that should
                     be recognized as translation functions
    :param comment_tags: a list of translator tags to search for and
                         include in the results
    :param options: a dictionary of additional options (optional)
    :return: an iterator over ``(lineno, funcname, message, comments)``
             tuples
    :rtype: ``iterator``
    """

''' TODO: Create a package with entry points
def setup(...
    entry_points = """
    [babel.extractors]
    xxx = your.package:extract_xxx
    """,
'''
