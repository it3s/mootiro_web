#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals  # unicode by default
import re


def extract_jquery_templates(fileobj, keywords, comment_tags, options):
    """Extracts translation messages from query template files.

    This is a plugin to Babel, written according to http://babel.edgewall.org/wiki/Documentation/0.9/messages.html#writing-extraction-methods

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
    # print 'Keywords: {}. Options: {}'.format(keywords, options)
    encoding = options.get('encoding', 'utf-8')
    comments = []
    funcname = message = None
    def new_regex(keyword, quote):
        # TODO: Allow plural messages, too
        return re.compile( \
            keyword + \
            "\("    +  # open parentheses to call function
            quote   +  # string start
            # TODO: Allow an escaped quote:
            "([^" + quote + "]+)" +  # capture: anything but a quote
            quote   +  # string end
            "\)"       # close parentheses (function call)
        )
    rx = []
    for keyword in keywords:
        rx.append(new_regex(keyword, '"'))
        rx.append(new_regex(keyword, "'"))
    # We have compiled our regular expressions, so now use them on the file
    for lineno, line in enumerate(fileobj, 1):
        line = line.decode(encoding)
        for r in rx:
            for match in r.finditer(line):
                yield (lineno, funcname, match.group(1), comments)
