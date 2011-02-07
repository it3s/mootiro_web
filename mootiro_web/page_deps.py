#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''page_deps.py

Copyright © 2011 Nando Florestan, Tiago Fassoni, Edgar Alvarenga

License: BSD

The problem: script and CSS linking in HTML, using various templates
====================================================================

If you develop web applications, you may have found yourself wondering how
to stop worrying about which stylesheets and javascript libraries
you should import in a given page, especially when that page is a composition
of fragments defined in various templates or functions.

There are 2 sides to this problem.
Worst of all is not declaring a library that is needed, 'cause then your
page does not work. But almost as bad is declaring everything you
might ever need in your master template -- because then, pages that don't need
heavy javascript libraries will be unnecessarily heavy and slow.

A solution is needed that allows you to first declare what you use, then on
each specific page, or even page fragment, declare what you need right there,
and the solution would generate the HTML imports, without repeating them.

We also must keep in mind that the order matters. For instance, jquery.ui
depends on jquery; and CSS has inheritance, so we need to link stylesheets
in the correct order.

The solution: PageDeps
======================

The following couple of classes are an attempt to solve that problem.
First of all, while you configure the application, you declare the files
that might be imported:

    deps_registry = DepsRegistry()
    deps_registry.lib('jquery', "/static/scripts/jquery-1.4.2.min.js")
    deps_registry.lib('deform', "/static/scripts/deform.js", depends='jquery')

The first argument to lib() -- and in fact to the other methods, too --
is a simple name for you to refer to the item later on.

As you can see, we can declare that deform.js depends on jquery. For more than
one dependency, you may use a list or a pipe:  depends="jquery|jquery.ui"

We also have a concept of a bottom_js: a javascript file that should be
declared at the bottom of the page, not at the top -- usually not a library,
but something "ad hoc" that might use libraries but might execute immediately,
relying on some HTML code. For instance:

    deps_registry.bottom_js('adhoctable',
                       "/static/scripts/add_features_to_a_certain_table.js",
                       depends='jquery')

What about CSS? Maybe there the declaration order will be enough?

    deps_registry.css('deform1', "/deform/css/form.css")
    deps_registry.css('deform2', "/deform/css/theme.css")

Actually, if you use, for example, the Deform library, you need to import
javascript files as well as CSS files, so we have a notion of a package:

    deps_registry.package('deform', css='deform1|deform2',
                          libs='deform', bottom_js=None)

OK, that is all for the registry, done at initialization time.

Now, for each new request, make sure your web framework instantiates
a PageDeps, passing it the deps_registry, and make it available to
controllers and templates. For instance, in the Pyramid web framework:

    @subscriber(interfaces.INewRequest)
    def on_new_request(event):
        event.request.page_deps = PageDeps(deps_registry)

After that, controller and view code can easily access the PageDeps instance
and do this kind of thing:

    # Use just one library:
    request.page_deps.lib('jquery')
    # Use a couple of stylesheets:
    request.page_deps.css('deform1')
    # Use just one bottom javascript file:

    # Or maybe import several stylesheets and javascript libraries:
    request.page_deps.package('deform')

Finally, to get the HTML output, you just include this inside the <head>
element of your master template:

    ${literal(request.page_deps.render_head())}

...and this at the bottom of the master template, for eventual javascript:

    ${literal(request.page_deps.render_bottom())}

I asked on IRC what other developers thought about this idea, you can read it
at __feedback__.
'''

# TODO: Update docs!


# http://docs.python.org/whatsnew/pep-328.html
from __future__ import absolute_import
from __future__ import print_function   # deletes the print statement
from __future__ import unicode_literals # unicode by default

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    from functools import total_ordering
except ImportError:
    def total_ordering(cls):
        """Class decorator that fills in missing ordering methods.

        http://code.activestate.com/recipes/576685/
        """
        convert = {
            b'__lt__': [(b'__gt__', lambda self, other: other < self),
                       (b'__le__', lambda self, other: not other < self),
                       (b'__ge__', lambda self, other: not self < other)],
            b'__le__': [(b'__ge__', lambda self, other: other <= self),
                       (b'__lt__', lambda self, other: not other <= self),
                       (b'__gt__', lambda self, other: not self <= other)],
            b'__gt__': [(b'__lt__', lambda self, other: other > self),
                       (b'__ge__', lambda self, other: not other > self),
                       (b'__le__', lambda self, other: not self > other)],
            b'__ge__': [(b'__le__', lambda self, other: other >= self),
                       (b'__gt__', lambda self, other: not other >= self),
                       (b'__lt__', lambda self, other: not self >= other)]
        }
        roots = set(dir(cls)) & set(convert)
        if not roots:
            raise ValueError('must define at least one ordering operation: < > <= >=')
        root = max(roots)       # prefer __lt__ to __le__ to __gt__ to __ge__
        for opname, opfunc in convert[root]:
            if opname not in roots:
                opfunc.__name__ = opname
                opfunc.__doc__ = getattr(int, opname).__doc__
                setattr(cls, opname, opfunc)
        return cls


class reify(object): # TODO: Remove
    """This code was stolen from Pyramid.
    Put the result of a method which uses this (non-data)
    descriptor decorator in the instance dict after the first call,
    effectively replacing the decorator with an instance variable.
    """
    def __init__(self, wrapped):
        self.wrapped = wrapped
        try:
            self.__doc__ = wrapped.__doc__
        except: # pragma: no cover
            pass

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val


@total_ordering
class Library(object):
    '''Represents a javascript library. Used internally.'''
    def __init__(self, name, url, dependencies=None):
        self.url = url
        self.name = name
        self.dependencies = dependencies

    def __gt__(self, other):
        '''Compare this Library instance to another (for sorting).
        Returns True if this instance is "greater than" the other
        (meaning it should be placed after the other).'''
        return other in self.dependencies

    def __repr__(self):
        '''Useful for debugging in ipython.'''
        return 'Library(name="{0}", url="{1}", dependencies={2})' \
            .format(self.name, self.url,
                    [d.name for d in self.dependencies])


@total_ordering
class Stylesheet(object):
    '''Represents a CSS stylesheet file. Used internally.'''
    def __init__(self, name, url, priority=100):
        self.url = url
        self.name = name
        self.priority = priority

    def __gt__(self, other):
        '''Compare this Stylesheet instance to another (for sorting).
        Returns True if this instance is "greater than" the other
        (meaning it should be placed after the other).'''
        return self.priority > other.priority

    def __repr__(self):
        '''Useful for debugging in ipython.'''
        return '{0}(name="{1}", url="{2}", priority={3})' \
            .format(type(self), self.name, self.url, self.priority)


class DepsRegistry(object):
    '''Should be used at web server initialization time to register every
    javascript and CSS file used by the application.

    The order of registration is important: it must be done bottom-up.

        deps_registry = DepsRegistry()
        deps_registry.lib('jquery', "/static/scripts/jquery-1.4.2.min.js")
        deps_registry.lib('deform', "/static/scripts/deform.js", depends='jquery')

    '''
    SEP = '|'

    def __init__(self,
                 profiles='development|production', profile='development'):
        '''*profiles* is a string containing server profiles separated by
        a pipe |.
        *profile* is the selected profile -- it typically comes from
        a configuration setting.

        Based on *profiles* and *profile* we select which URL to use for each
        javascript library.
        '''
        i = 0
        for s in profiles.split(self.SEP):
            if s == profile:
                self._profile = i
                break
            i += 1
        if not hasattr(self, '_profile'):
            raise RuntimeError('Profile "{0}" not in "{1}".' \
                               .format(profile, profiles))
        self._css = {}
        self._libs = {}
        self._packages = {}
        self._css_priority = 0 # this autoincrements :)

    def lib(self, name, urls, depends=[]):
        '''If provided, the *depends* argument must be either a list of strings,
        or one string separated by pipes: |

        Same can be said of the *urls* parameter.

        Each of these items must be the name of another library,
        required for this library to work.
        '''
        if hasattr(self._libs, name):
            raise RuntimeError \
                ('Library "{0}" already registered.'.format(name))
        # Recursively list all the dependencies, and
        # swap dependency names with actual Library objects
        deplibs = []
        if isinstance(depends, basestring):
            depends = depends.split(self.SEP)
        if depends:
            for depname in depends:
                self._recursively_add_deps(depname, deplibs)
        if isinstance(urls, basestring):
            urls = urls.split(self.SEP)
        self._libs[name] = Library(name, urls[self._profile], deplibs)

    def _recursively_add_deps(self, libname, out_list):
        try:
            lib = self._libs[libname]
        except KeyError:
            raise KeyError('Dependency "{0}" not yet registered.' \
                           .format(libname))
        for dep in lib.dependencies:
            self._recursively_add_deps(dep.name, out_list)
        if lib not in out_list:
            out_list.append(lib)

    def stylesheet(self, name, urls, priority=None):
        if isinstance(urls, basestring):
            urls = urls.split(self.SEP)
        self._css_priority += 1
        self._css[name] = Stylesheet(name, urls[self._profile],
                                     priority or self._css_priority)

    def package(self, name, libs=[], css=[], onload=''):
        self._packages[name] = (libs, css, onload)


class PageDeps(object):
    '''Represents the dependencies of a page; i.e. CSS stylesheets,
    javascript libraries and javascript onload code.
    Easy to declare and provides the HTML tag soup.
    '''
    def __init__(self, registry):
        self._reg = registry
        self._css = []
        self._libs = []
        self.onloads = []

    def lib(self, name):
        '''Adds a requirement of a javascript library to this page,
        if not already there.
        '''
        lib = self._reg._libs[name]
        if lib not in self._libs:
            self._libs.append(lib)

    def libs(self, names):
        '''Adds requirements for a few javascript libraries to this page,
        if not already there.
        '''
        if isinstance(names, basestring):
            names = names.split('|')
        for name in names:
            self.lib(name)

    @property
    def sorted_libs(self):
        '''Recommended for use in your templating language. Returns a list of
        the URLs for the javascript libraries required by this page.
        '''
        flat = []
        for lib in self._libs:
            for dep in lib.dependencies:
                if dep.url not in flat:
                    flat.append(dep.url)
            if lib.url not in flat:
                flat.append(lib.url)
        return flat

    @property
    def out_libs(self):
        '''Returns a string containing the script tags.'''
        return '\n'.join(['<script type="text/javascript" src="{0}"></script>' \
            .format(url) for url in self.sorted_libs])

    def stylesheet(self, name):
        '''Adds a requirement of a CSS stylesheet to this page, if not
        already there.
        '''
        css = self._reg._css[name]
        if css not in self._css:
            self._css.append(css)

    def stylesheets(self, names):
        '''Adds requirements for a few CSS stylesheets to this page,
        if not already there.
        '''
        if isinstance(names, basestring):
            names = names.split('|')
        for name in names:
            self.stylesheet(name)

    @property
    def sorted_stylesheets(self):
        '''Recommended for use in your templating language. Returns a list of
        the URLs for the CSS stylesheets required by this page.
        '''
        return [s.url for s in sorted(self._css)]

    @property
    def out_stylesheets(self):
        '''Returns a string containing the CSS link tags.'''
        CSS_TAG = '<link rel="stylesheet" type="text/css" href="{0}" />'
        return '\n'.join([CSS_TAG.format(url) for url in
                          self.sorted_stylesheets])

    def onload(self, code):
        '''Adds some javascript onload code.'''
        self.onloads.append(code)

    def out_onloads(self, tag=False, jquery=False):
        if not self.onloads:
            return '\n'
        s = StringIO()
        if tag:
            s.write('<script type="text/javascript">\n')
        if jquery:
            s.write('$(function() {\n')
        for o in self.onloads:
            s.write(o)
            s.write('\n')
        if jquery:
            s.write('});\n')
        if tag:
            s.write('</script>\n')
        return s.getvalue()

    def package(self, name):
        '''Require a package.'''
        libs, css, onload = self._reg._packages[name]
        self.libs(libs)
        self.stylesheets(css)
        if callable(onload):
            self.onload(onload())
        else:
            self.onload(onload)

    def __unicode__(self):
        return '\n'.join([self.out_stylesheets, self.out_libs,
                          self.out_onloads(tag=True, jquery=True)])


'''Tests'''
if __name__ == '__main__':
    r = DepsRegistry()
    r.lib('jquery', ['http://jquery'])
    r.stylesheet('jquery', 'http://jquery.css')
    r.lib('jquery.ui', 'http://jquery.ui', 'jquery')
    r.lib('jquery.ai', 'http://jquery.ai', 'jquery.ui')
    r.lib('deform', 'http://deform.js', 'jquery')
    r.stylesheet('deform', 'http://deform.css')
    r.lib('triform', 'http://triform.js', 'deform|jquery.ui')
    r.package('triform', libs='triform', css='deform')
    print('\n=== Registry ===')
    from pprint import pprint
    pprint(r._libs)
    print('\n=== Page ===')
    p = PageDeps(r)
    p.package('triform')
    p.libs('deform')
    print(p.out_libs)
    p.stylesheets('deform|jquery|deform')
    print(p.out_stylesheets)
    p.onload('// some javascript code here...')
    print(p.out_onloads(tag=True, jquery=True))
    print('\n=== All ===')
    print(unicode(p))


__all__ = ['DepsRegistry', 'PageDeps']


__feedback__ = '''
<nandoflorestan> Does anyone know any code for creating a kind of registry for CSS imports and/or JavaScript imports, and dynamically dealing with their dependencies?
<benbangert> nandoflorestan: not offhand, toscawidgets has some stuff to try and track repeat CSS/JS includes and such
<nandoflorestan> http://code.google.com/p/bag/source/browse/bag/web/html_imports.py

<benbangert> nandoflorestan: I guess the reason I shy away from that is its inefficient to have a bunch of CSS/JS links on a page
<benbangert> I usually put all the JS required for the entire site together in one file, minimize the crap out of it, and serve it once with a super long expires
<benbangert> same with CSS
<mgedmin> it would be shiny to have the framework do that for me
<mgedmin> bunch of .js and .css files in my source tree --> automatic collection + minification + caching of minified version on disk + serving with long expiration date and hash/timestamp in url
<rmarianski> some guys worked on some middleware at some point in the past to do that
<rmarianski> http://svn.repoze.org/repoze.squeeze/trunk/
<rmarianski> i'm not sure what the status of that is currently though
<rmarianski> looks like malthe did most of it
<RaFromBRC> :)
<blaflamme> marianski, that middleware looks good

<benbangert> but I know for many uses that just doesn't work
<benbangert> so I definitely see the utility of something like that
<RaFromBRC> nandoflorestan: yeah, i think it looks useful... i've used similar tools in other systems
<gjhiggins> nandoflorestan: headbottom would be useful
<ScottA> nandoflorestan: That looks very useful. Having registry.head_bottom would be semantically nice
<ScottA> Or something to that effect
<nandoflorestan> Why is head_bottom useful if we have dependency checking?
<gjhiggins> nandoflorestan: less work for the dev
<nandoflorestan> just tell me how so, just so I know we are on the same page here
<ScottA> Pure semantics. There's some javascript stuff I like to stick in the head that isn't library code. jQuery(document).ready(), data structures, that sort of thing
<nandoflorestan> ScottA, thanks, I understand it better after what you said.
<nandoflorestan> oh wait, what about javascript literals (not external files)
<nandoflorestan> I guess those are out of the scope huh
<ScottA> Probably
<ScottA> You could accept python data structures and convert then to JSON, maybe
<ScottA> Might be useful for people who like to use dynamic javascript
'''

