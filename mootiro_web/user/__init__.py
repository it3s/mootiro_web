#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''User management models, schemas and views for Pyramid.'''

from __future__ import unicode_literals  # unicode by default
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import get_localizer, TranslationStringFactory
from pyramid.renderers import get_renderer
from pyramid.url import route_url

_ = TranslationStringFactory('mootiro_web')
del TranslationStringFactory


class BaseView(object):
    '''Base class for views.'''

    def __init__(self, request):
        self.request = request

    @reify
    def tr(self):
        return get_localizer(self.request).translate

    def url(self, name, *a, **kw):
        '''A route_url that is easier to use.'''
        return route_url(name, self.request, *a, **kw)

    def model_to_dict(self, model, keys):
        '''Helps when using Deform.'''
        d = {}
        for k in keys:
            val = getattr(model, k)
            d[k] = val if val else ''
        return d

    def dict_to_model(self, adict, model):
        '''Helps when using Deform.'''
        for key, val in adict.items():
            setattr(model, key, val)
        return model


class ChameleonBaseView(BaseView):
    '''Base view for projects that use Chameleon with macros.'''
    macro_cache = {}

    @classmethod
    def macro(cls, template, macro_name):
        '''Loads macros from any template and memoizes them.'''
        macro_path = template + '|' + macro_name
        macro = cls.macro_cache.get(macro_path)
        if not macro:
            cls.macro_cache[macro_path] = macro = \
                get_renderer(template).implementation().macros[macro_name]
        return macro


def authenticated(func):
    '''Decorator that redirects to the login page if the user is not yet
    authenticated.
    '''
    def wrapper(self, *a, **kw):
        if self.request.user:
            return func(self, *a, **kw)
        else:
            referrer = self.request.path
            return HTTPFound(location=self.url('user', action='login',
                _query=[('ref', referrer)]))
    return wrapper


def get_request_class(deps, settings, User=None, sas=None):
    '''Sets which user model shall be used according to configuration,
    sets the user salt if necessary (also according to configuration),
    and returns a nice Request class which uses PageDeps and memoizes the
    user object.
    '''
    if not User:
        from .models import user as user_module
        if settings.get('CAS.enable') == 'true':
            user_module.User = User = user_module.make_user_class(full=False)
        else:
            user_module.User = User = user_module.make_user_class(full=True)
            # The User model requires a per-installation salt (a string)
            # for creating user passwords hashes, so:
            User.salt = settings.pop('auth.password.hash.salt')  # required config

    from pyramid.request import Request
    from pyramid.security import authenticated_userid
    from ..page_deps import PageDeps
    if not sas:
        from .models.user import sas

    class MootiroRequest(Request):
        def __init__(self, *a, **kw):
            super(MootiroRequest, self).__init__(*a, **kw)
            self.page_deps = PageDeps(deps)

        @reify
        def user(self):
            '''Memoized user object. If we always use request.user to retrieve
            the authenticated user, the query will happen only once per request,
            which is good for performance.
            '''
            userid = authenticated_userid(self)
            return sas.query(User).get(userid) if userid else None

    return MootiroRequest


def create_locale_cookie(locale, settings):
    for loc in settings['enabled_locales']:
        if loc['name'] == locale:
            headers = [(b'Set-Cookie',
                b'_LOCALE_={0}; expires=Fri, 31-Dec-9999 23:00:00 GMT; Path=/' \
                .format(locale.encode('utf8')))]
            return headers
    raise KeyError('Locale not configured: "{}"'.format(locale))


def enable_auth(settings, config):
    if settings.get('CAS.enable') == 'true':
        # Raise KeyError if configuration is missing:
        settings['CAS.url']
        settings['CAS.profile.url']
        from .views import CasView
        CasView.add_routes(config)
    else:
        from .views import UserView
        UserView.add_routes(config)
        if settings.get('genshi_renderer'):
            raise RuntimeError('Call enable_genshi() after enable_auth().')
        # Add our templates directory to the Genshi search path
        dirs = settings.get('genshi.directories', [])
        if isinstance(dirs, basestring):
            dirs = [dirs]
        dirs.append('mootiro_web:user/templates')
        settings['genshi.directories'] = dirs
