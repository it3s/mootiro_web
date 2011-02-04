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
one dependency, you may use a comma:  depends="jquery,jquery.ui"

We also have a concept of a bottom_js: a javascript file that should be
declared at the bottom of the page, not at the top -- usually not a library,
but something "ad hoc" that might use libraries but might execute immediately,
relying on some HTML code. For instance:

    deps_registry.bottom_js('adhoctable',
                       "/static/scripts/add_features_to_a_certain_table.js",
                       depends='jquery')

What about CSS? Maybe there a numerical priority will be enough?

    deps_registry.css('deform_css',
        ["/deform/css/form.css", "/deform/css/theme.css"], priority=100)

Actually, if you use, for example, the Deform library, you need to import
javascript files as well as CSS files, so we have a notion of a package:

    deps_registry.package('deform', css='deform_css',
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
    request.page_deps.require_lib('jquery')
    # Use just one stylesheet:
    request.page_deps.require_css('deform_css')
    # Use just one bottom javascript file:
    # Or maybe import several stylesheets and javascript libraries:
    request.page_deps.require_package('deform')

Finally, to get the HTML output, you just include this inside the <head>
element of your master template:

    ${literal(request.page_deps.render_head())}

...and this at the bottom of the master template, for eventual javascript:

    ${literal(request.page_deps.render_bottom())}

I asked on IRC what other developers thought about this idea, you can read it
at __feedback__.
'''


# http://docs.python.org/whatsnew/pep-328.html
from __future__ import absolute_import
from __future__ import print_function   # deletes the print statement
from __future__ import unicode_literals # unicode by default


class reify(object):
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


class Library(object):
    '''Represents a javascript library. Used internally.'''
    def __init__(self, name, url, adict, dependencies=None):
        self.url = url
        self.name = name
        self.adict = adict
        self.dependency_names = dependencies
    
    @reify
    def dependencies(self):
        alist = []
        for name in self.dependency_names:
            alist.append(self.adict[name])
        return alist # of actual Library objects
    
    def __lt__(self, other):
        '''Compare this Library instance to another (for sorting).'''
        raise NotImplementedError()


class DepsRegistry(object):
    '''Should be used at web server initialization time to register every
    javascript and CSS file used by the application.
    '''
    def __init__(self, profile=0):
        '''*profile* is an integer specifying which index to use from the
        URL list.
        '''
        self._profile = profile
        self._css = {}
        self._libs = {}
        self._packages = {}
    
    def lib(self, name, urls, depends=None):
        if hasattr(self._libs, name):
            raise RuntimeError \
                ('Library "{0}" already registered.'.format(name))
        self._libs[name] = Library(name, urls[self.profile], dependencies)
    
    def css(self, name, urls, priority=100):
        self._css[name] = (urls, priority)
    
    def package(self, name, libs=[], css=[]):
        self._packages[name] = (libs, css)


class PageDeps(object):
    def __init__(self, registry):
        self._reg = registry
        self._css = []
        self._libs = []
        self._onloads = []
        self._packages = []
    
    def onload(self, code):
        '''Adds some javascript onload code.
        '''
        self._onloads.append(code)

    def lib(self, name):
        '''Adds a requirement of a javascript library to this page,
        if not already there.
        '''
        if name not in self._libs:
            self._libs.append(name)

    def css(self, name):
        '''Adds a requirement of a CSS stylesheet to this page, if not
        already there.
        '''
        if name not in self._css:
            self._css.append(name)

    @property
    def sorted_libs(self):
        flat = []
        for name in self._libs:
            lib = self._reg._libs[name]
            for dep in lib.dependencies:
                if dep not in flat:
                    flat.append(dep)
        # Now flat contains all the required js files -- multiple times.
        return sorted(set(flat)) # Well, remove the repetitions and sort

    def package_require(self, name):
        ''' This function returns the files defined as a package, except those already loaded
        
        '''
        if self._things_already_required.has_key(name):
            return True
        
        for key, value in self._packages.items():
            for javascript in value[0]:
                if not self._things_already_required.has_key(javascript):
                    self._sorted_js.append(javascript)
                    self._things_already_required[javascript] = "REQ" 
            for css in value[1]:
                if not self._things_already_required.has_key(css):
                    self._sorted_css.append(css)
                    self._things_already_required[css] = "REQ"
        # Not a beautiful iteration, but inherited from my times as a
        # C developer

    def onload_require(self, name):
        if self._things_already_required.has_key(name):
            return True

        self._sorted_onload.append(name)
        self._things_already_required[name] = "REQ"

    def js_export(self):
        '''This function dispatchs all the javascript files in the _sorted_js
        variable
        '''
        output = ''
        for js in self._sorted_js:
            output += '<script type="text/javascript" src="%s"/>' % js[1]
        return output

    def css_export(self):
        '''This function simply dispatchs all the css files in the _sorted_css variable '''
        self._sorted_css = sorted(self._sorted_css, key = lambda css_package: css_package[2])
        output = ''
        
        for css in self._sorted_css:
            output += '<link rel="stylesheet" type="text/css" href="%s"/>' % css[1]
        return output





    def __init__(self): #, registry):
        #self._reg = registry
        pass
        # Checar se há arquivos!
        # Checar dependências dos arquivos
        # 
        # Ordenar os arquivos CSS
        



# class HtmlImports(object):
#     '''Well, how do you like the specification?
#     nandoflorestan @ #pyramid wants to know  :)    
#     Aqui é onde tudo é incluído, ordenado e requisitado!
#     '''



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

