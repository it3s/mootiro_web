#!/usr/bin/env python
# -*- coding: utf-8 -*-


doc_do_tiago = '''

Parada é a seguinte: tem a função 

import_js(alias, string, depends) 

Essa coisa importa um, APENAS UM E SOMENTE UM javascript por vez

e outra que é o import_css(alias, string, funcao) que importa somente um css por vez

Aí posso definir o lindo package, que faz o seguinte:

package_import(alias="meuPacoteAwesome", js='jquery','jqueryui', css='jqueryCSS','jqueryuiCSS')

Os CSS têm prioridades, os javascripts dependencias, e agora eu tenho que pensar num jeito legal de fazer essa porra toda sair.

Além disso, tenho que ver como fazer com os CSS aleatorios que sao executados em cada script, que nao entendi direito 

TODO 2011-01-27: Colocar um treco de importação de strings, para o momento do javascript onLoad 

'''

# http://docs.python.org/whatsnew/pep-328.html
from __future__ import absolute_import
from __future__ import print_function   # deletes the print statement
from __future__ import unicode_literals # unicode by default


class Registry(object):
    '''This is the big class containing all the import methods and the require
    methods.
    '''
    _all_js = {}
    _packages = {}
    _all_css = {}
    _sorted_css = []
    _sorted_js = []
    _onload = {}
    _sorted_onload = []
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
        ''' The bigger the priority, the last it will be executed. For
        instance, the file having priority=0 is the first, priority=1 the
        second.... 
        This function must be used for one archive at a time only.    
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

    def onload_import(self, alias = '', text = ''):
        ''' This method imports a javascript onload definition 

        '''
        self._onload[alias] = text 

    def js_remove(self, alias=''):
        del self._all_js[alias]

    def css_remove(self, alias=''):
        del self._all_css[alias]
 
    def package_remove(self, alias=''):
        del self._all_js[alias]

    def js_require(self, name = ''):
        ''' Returns a Javscript library
            TODO: Make it work with multiple dependencies
        '''
        #First of all, we check if the library is already loaded
        if self._things_already_required[name]:
            return True
        #The rest of the checks comes free from Python
        self._sorted_js.append((name, self._all_js[name][0],
            self._all_js[name][1]))
    
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
        if self._things_already_required[name]:
            return True
        
        for key, value in self._packages.items():
            for javascript in value[0]:
                if not self._things_already_required[javascript]:
                    self._sorted_js.append(javascript)
                    self._things_already_required[javascript] = "REQ" 
            for css in value[1]:
                if not self._things_already_required[css]:
                   self._sorted_css.append(css)
                   self._things_already_required[css] = "REQ"
        # Not a beautiful iteration, but inherited from my times as a
        # C developer

    def onload_require(self, name):
        if self._things_already_required[name]:
            return True

        self._sorted_onload.append(name)
        self._things_already_required[name] = "REQ"

    def ready_set_go(self):
        '''This function simply dispatchs all the css files in the _sorted_css variable '''
        self._sorted_css = sorted(self._sorted_css, key = lambda css_package: css_package[2])
        for i in self._sorted_css:
            print(i)
        for i in self._sorted_js:
            print(i)
        for i in self._sorted_onload:
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

