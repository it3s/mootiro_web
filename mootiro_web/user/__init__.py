#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''User management models, schemas and views for Pyramid.'''

from __future__ import unicode_literals  # unicode by default
from pyramid.decorator import reify
from pyramid.url import route_url
from pyramid.i18n import get_localizer, TranslationStringFactory

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


def get_request_class(deps):
    from pyramid.request import Request
    from pyramid.security import authenticated_userid
    from .models.user import User, sas
    from ..page_deps import PageDeps

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
