#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''http://code.google.com/p/bag/source/browse/bag/web/html_imports.py

Copyright © 2011 Nando Florestan

License: BSD

The problem: script and CSS linking in HTML, using various templates
====================================================================

 f you develop web applications, you may have found yourself wondering how
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
and the solution would generate the HTML imports.

We also must keep in mind that the order matters. For instance, jquery.ui
depends on jquery; and CSS has inheritance, so we need to link stylesheets
in the correct order.

The solution: HtmlImports
=========================

The following couple of classes are an attempt to solve that problem.
First of all, while you configure the application, you declare the files
that might be imported:

    registry = HtmlImportsRegistry()
    registry.lib('jquery', "/static/scripts/jquery-1.4.2.min.js")
    registry.lib('deform', "/static/scripts/deform.js", depends='jquery')

The first argument to lib() -- and in fact to the other methods, too --
is a simple name for you to refer to the item later on.

As you can see, we can declare that deform.js depends on jquery. For more than
one dependency, you may use a comma:  depends="jquery,jquery.ui"

We also have a concept of a _bottom_jss: a javascript file that should be
declared at the bottom of the page, not at the top -- usually not a library,
but something "ad hoc" that might use libraries but might execute immediately,
relying on some HTML code. For instance:

    registry._bottom_jss('adhoctable',
                       "/static/scripts/add_features_to_a_certain_table.js",
                       depends='jquery')

What about CSS? Maybe there a numerical priority will be enough?

    registry.css('deform_css',
                 ["/deform/css/form.css", "/deform/css/theme.css"], priority=100)

Actually, if you use, for example, the Deform library, you need to import
javascript files as well as CSS files, so we have a notion of a package:

    registry.package('deform', css='deform_css', libs='deform', _bottom_jss=None)

OK, that is all for the registry, done at initialization time.

Now, make sure your web framework instantiates an HtmlImports, passing it the
registry, and make it available to controllers and templates. For instance,
in the Pyramid web framework:

    @subscriber(interfaces.INewRequest)
    def on_new_request(event):
        event.request.html_imports = HtmlImports(registry)

After that, controller and view code can easily access the HtmlImports instance 
and do this kind of thing:

    # Use just one library:
    request.html_imports.require_lib('jquery')
    # Use just one stylesheet:
    request.html_imports.css_require('deform_css')
    # Use just one bottom javascript file:
    # Or maybe import several stylesheets and javascript libraries:
    request.html_imports.require_package('deform')

Finally, to get the HTML output, you just include this inside the <head>
element of your master template:

    ${literal(request.html_imports.render_head())}

...and this at the bottom of the master template, for eventual javascript:

    ${literal(request.html_imports.render_bottom())}

  asked on IRC what other developers thought about this idea, you can read it
at __feedback__.
'''
doc_do_tiago = '''

Parada é a seguinte: tem a função 

import_js(alias, string, depends) 

Essa coisa importa um, APENAS UM E SOMENTE UM javascript por vez

e outra que é o import_css(alias, string, funcao) que importa somente um css por vez

Aí posso definir o lindo package, que faz o seguinte:

package_import(alias="meuPacoteAwesome", js='jquery','jqueryui', css='jqueryCSS','jqueryuiCSS')

Os CSS têm prioridades, os javascripts dependencias, e agora eu tenho que pensar num jeito legal de fazer essa porra toda sair.

Além disso, tenho que ver como fazer com os CSS aleatorios que sao executados em cada script, que nao entendi direito 

'''

# http://docs.python.org/whatsnew/pep-328.html
from __future__ import absolute_import
from __future__ import print_function   # deletes the print statement
from __future__ import unicode_literals # unicode by default


class Registry(object):
    '''Aqui é a classe fodona que contém tudo. Não só tem todas as classes de importação, como tem todas as classes de uso e o registro geral 
    As funções de ordenação do registro também ficam aqui
    '''
    _all_js = {}
    _packages = {}
    _all_css = {}
    _sorted_css = []
    _sorted_js = []
 #   _bottom_js = {}
    _things_already_required = {}

     

    def js_import(self, alias = '', path = '', depends=None):
        ''' This method imports javascript files. It only accepts a file at a time. Then the javascript goes to an internal registry.
        '''
        #First of all, let's check the input
        if type(alias) != str: 
            raise Exception("Alias must be a string") 

        if not path:
            raise Exception("Path must not be empty")
#        if depends:
#            if not _all_js[depends]:
#                raise Exception("Your dependency has not been registered yet")

        self._all_js[alias] = (path,depends)
    

    def css_import(self, alias = '', path = '', priority=100):
        ''' Quanto maior a prioridade, por ultimo sera executado. Por exemplo, o arquivo com priority=0 é o primeiro, priority=1 o segundo...
        Essa função pode ser usada tanto para um pacote inteiro ou somente um arquivo.    
            '''
        if type(alias) != str:
            raise Exception("Alias must be a string")
        if not path:
            raise Exception("Path must not be empty")
        
        self._all_css[alias] = (path, priority)
        

    def package_import(self, alias = '', js = [], css = [] ):
        '''This method registers a lot of aliases as a package. Usage is: 
        package_import(alias = TODO: This function seems unnecessary.  Imports a bunch of files at a time. Those files are the first to be loaded, and are stored with the javascript files. 
        Why? Because have to be placed in the Javascript variable because of dependencies '''
        #Okay, I won't check anything, I'm lazy
        self._all_js[alias] = (js, css)

    def js_remove(self, alias=''):
        del self._all_js[alias]

    def css_remove(self, alias=''):
        del self._all_css[alias]
 
    def package_remove(self, alias=''):
        del self._all_js[alias]
    
#    def js_require(self, name = ''):
#       '''Returns a Javascript library
#       TODO: Make it work with multiple dependencies
#       '''
#       #First of all, we check if the library is already loaded
#       if self._things_already_required[name]:
#           return True
#       #The rest of the checks comes free from Python
#       if self._all_js[name][1] != None:
#           for i in self._all_js[name][1]:
#               js_require(i)
#       _sorted_js.append((name, self._all_js[name][0], self._all_js[name][1]))
#       return True

    def css_require(self, name = ''):
        ''' This function prepares a variable containing all the necessary css files  '''
        #Edgar, favor rever aqui!!
        if self._things_already_required[name]:
            return True
        self._sorted_css.append((name, self._all_css[name][0],self._all_css[name][1]))

    def package_require(self, name = ''):
        ''' This function returns the files defined as a package, except those already loaded
        
        '''
       

    def ready_set_go(self):
        '''This function simply dispatchs all the css files in the _sorted_css variable '''
        self._sorted_css = sorted(self._sorted_css, key = lambda css_package: css_package[2])
        for i in self._sorted_css:
            print(i)
        for i in self.sorted_js:
            print(i)



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

