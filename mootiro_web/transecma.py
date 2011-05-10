#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Transecma is a Python solution for javascript internationalization,
written in 2011 by Nando Florestan.

Babel already has a javascript extractor (a function that goes through
javascript code finding translation strings and writing them to a
.POT translation template file).
In this module there is a jquery template extractor, so if you use jquery
templates, they can be internationalized using traditional gettext tools.

The .pot file can be converted to .po files using Babel or GNU gettext.
Each of these .po files is to contain a translation to one language.
These .po files are edited by translators in special utilities such as poedit.

This file also contains po2json, a command that converts .PO
translation files into javascript JSON files, so the translation may happen
on the client, in a browser, through javascript code.

Transecma does *not* help you with the problem of adding to your pages
a <script> tag that loads the javascript file that contains the translations
that correspond to your user's locale. This problem depends on which
web framework you are using, but it should be very easy to solve.

The final part of the solution is transecma.js, a javascript file that
contains functions to perform translations based on the
translation dictionary discussed above, as well as interpolate them
with values from your application.
'''


from __future__ import unicode_literals  # unicode by default
import os
import re


def exists(path):
    """Test whether a path exists.  Returns False for broken symbolic links.
    """
    try:
        os.stat(path)
    except os.error:
        return False
    return True


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


def po2dict(stream, locale, use_fuzzy=False):
    '''Given a `stream` (a file-like object) and a locale, returns a
    dictionary of the message IDs and translation strings.
    '''
    from babel.messages.pofile import read_po
    catalog = read_po(stream, locale)
    messages = [m for m in catalog if m.string]
    if not use_fuzzy:
        messages[1:] = [m for m in messages[1:] if not m.fuzzy]
    messages.sort()
    return {message.id: message.string for message in messages}


def make_json(structure, variable_name=None, indent=1, **k):
    '''Converts something into a json string, optionally attributing the result
    to a variable.

    It also escapes the forward slash, making the result suitable
    to be included in an HTML <script> tag.
    '''
    import json
    s = json.dumps(structure, indent=indent, **k).replace('/', '\/')
    return "{0} = {1};\n".format(variable_name, s) if variable_name \
        else s


def po2json(po_path, locale, variable_name=None, use_fuzzy=None):
    '''Compiles one .po file into JSON and returns the resulting string.'''
    with open(po_path) as file:
        d = po2dict(file, locale, use_fuzzy=use_fuzzy)
    return make_json(d, variable_name=variable_name)


def compile_dir(dir, domain, out_dir, variable_name=None, use_fuzzy=None,
                encoding='utf8'):
    import codecs
    jobs = []
    if not exists(out_dir):
        os.makedirs(out_dir)
    for locale in os.listdir(dir):
        po_path = os.path.join(dir, locale, 'LC_MESSAGES', domain + '.po')
        if os.path.exists(po_path):
            out_path = os.path.join(out_dir, locale + '.js')
            jobs.append((locale, po_path, out_path))
    for locale, po_path, out_path in jobs:
        print('    Creating {0}'.format(out_path))
        s = po2json(po_path, locale, variable_name=variable_name,
            use_fuzzy=use_fuzzy)
        with codecs.open(out_path, 'w', encoding=encoding) as writer:
            writer.write(s)


def po2json_command():
    '''This function is an entry point; it is turned into a console script
    when the package is installed.

    po2json is a command that converts .PO translation files into javascript
    JSON files. This is a step in web application internationalization.

    Example usage:

        po2json -D $DOMAIN -d $OUTDIR -o $JS_DIR -n mfTranslations

    For help with the arguments, type:

        po2json -h
    '''
    from argparse import ArgumentParser
    p = ArgumentParser(description='Converts .po files into .js files ' \
        'for web application internationalization.')
    p.add_argument('--domain', '-D', dest='domain', default='messages',
                   help="domain of PO files (default '%(default)s')")
    p.add_argument('--directory', '-d', dest='dir',
                   metavar='DIR', help='base directory of catalog files')
    p.add_argument('--output-dir', '-o', dest='out_dir', metavar='DIR',
                   help="name of the output directory for .js files")
    p.add_argument('--use-fuzzy', '-f', dest='use_fuzzy', action='store_true',
                   default=False,
                   help='also include fuzzy translations (default %(default)s)')
    p.add_argument('--variable', '-n', dest='variable_name', default=None,
                   help="javascript variable name for the translations object")
    d = p.parse_args()
    if not d.dir:
        p.print_usage()
        return
    compile_dir(d.dir, d.domain, d.out_dir, variable_name=d.variable_name,
                use_fuzzy=d.use_fuzzy)


if __name__ == '__main__':
    po2json_command()
