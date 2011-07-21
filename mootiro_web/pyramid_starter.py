#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals  # unicode by default
import os
import stat


def isdir(s):
    """Return true if the pathname refers to an existing directory."""
    try:
        st = os.stat(s)
    except os.error:
        return False
    return stat.S_ISDIR(st.st_mode)


def makedirs(s):
    '''Make directories (if they don't exist already).'''
    if not isdir(s):
        os.makedirs(s)


class PyramidStarter(object):
    '''Reusable configurator for nice Pyramid applications.'''

    def __init__ (self, name, __file__, settings, config,
                  require_python27=False):
        '''The first positional argument should be, simply, __file__ (in other
        words, a string containing the path to the file that represents the
        Pyramid app).

        `name` is the name of your package;
        `config` is the Pyramid configurator instance, or a dictionary that
        can be used to create such an instance.
        '''
        self.name = name
        if require_python27:
            self.require_python27()
        if isinstance(config, dict):
            self.make_config(config, settings)
        self.directory = os.path.abspath(os.path.dirname(__file__))
        self.parent_directory = os.path.dirname(self.directory)
        from importlib import import_module
        self.module = import_module(self.name)
        # Create the _() function for internationalization
        from pyramid.i18n import TranslationStringFactory
        self._ = TranslationStringFactory(name)

    def make_config(self, adict, settings):
        """Creates *config*, a temporary wrapper of the registry.
        This method is intended to be overridden in subclasses.
        `adict` should contain request_factory, session_factory,
        authentication_policy, authorization_policy etc.
        """
        from pyramid.config import Configurator
        adict.setdefault('settings', settings)
        self.config = config = Configurator(**adict)

    @property
    def settings(self):
        return self.config.get_settings()

    def makedirs(self, key):
        '''Creates a directory if it does not yet exist.
        The argument is a string that may contain one of these placeholders:
        {here} or {up}.
        '''
        makedirs(key.format(here=self.directory, up=self.parent_directory))

    def log(self, text):
        '''TODO: Implement logging setup'''
        print(text)

    def enable_handlers(self, scan=True):
        '''Pyramid "handlers" emulate Pylons 1 "controllers".
        https://github.com/Pylons/pyramid_handlers
        '''
        from pyramid_handlers import includeme
        self.config.include(includeme)
        if scan:
            self.config.scan(self.name)

    def enable_sqlalchemy(self, initialize_sql=None):
        from sqlalchemy import engine_from_config
        self.engine = engine = engine_from_config(self.settings, 'sqlalchemy.')
        if not initialize_sql:
            from importlib import import_module
            try:
                module = import_module(self.name + '.models')
            except ImportError as e:
                self.log('Could not find the models module.')
            else:
                try:
                    initialize_sql = module.initialize_sql
                except AttributeError as e:
                    self.log('initialize_sql() does not exist.')
        if initialize_sql:
            self.log('initialize_sql()')
            initialize_sql(engine, settings=self.settings)

    def enable_turbomail(self):
        from turbomail.control import interface
        import atexit
        options = {key: self.settings[key] for key in self.settings \
            if key.startswith('mail.')}
        interface.start(options)
        atexit.register(interface.stop, options)

    def enable_kajiki(self):
        '''Allows you to use the Kajiki templating language.'''
        from mootiro_web.pyramid_kajiki import renderer_factory
        for extension in ('.txt', '.xml', '.html', '.html5'):
            self.config.add_renderer(extension, renderer_factory)

    def enable_genshi(self):
        '''Allows us to use the Genshi templating language.
        We intend to switch to Kajiki down the road, therefore it would be
        best to avoid py:match.
        '''
        self.settings.setdefault('genshi.translation_domain', self.name)
        from mootiro_web.pyramid_genshi import renderer_factory
        self.config.add_renderer('.genshi', renderer_factory)

    def configure_favicon(self, path='static/icon/32.png'):
        from mimetypes import guess_type
        from pyramid.resource import abspath_from_resource_spec
        self.settings['favicon'] = path = abspath_from_resource_spec(
            self.settings.get('favicon', '{}:{}'.format(self.name, path)))
        self.settings['favicon_content_type'] = guess_type(path)[0]

    def enable_internationalization(self, extra_translation_dirs):
        self.makedirs(self.settings.get('dir_locale', '{here}/locale'))
        self.config.add_translation_dirs(self.name + ':locale',
            *extra_translation_dirs)
        # from pyramid.i18n import default_locale_negotiator
        # self.config.set_locale_negotiator(default_locale_negotiator)

    def result(self):
        '''Commits the configuration (this causes some tests) and returns the
        WSGI application.
        '''
        return self.config.make_wsgi_app()

    @property
    def all_routes(self):
        '''Returns a list of the routes configured in this application.'''
        return all_routes(self.config)

    def require_python27(self):
        '''Demand Python 2.7 (ensure not trying to run it on 2.6.).'''
        from sys import version_info, exit
        version_info = version_info[:2]
        if version_info < (2, 7) or version_info >= (3, 0):
            exit('\n' + self.name + ' requires Python 2.7.x.')


def all_routes(config):
    '''Returns a list of the routes configured in this application.'''
    return [(x.name, x.pattern) for x in \
            config.get_routes_mapper().get_routes()]
