#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals  # unicode by default
from httplib import HTTPConnection
from urllib import urlencode
from pyramid.security import remember, forget
from pyramid.httpexceptions import HTTPFound


class BaseAuthenticator(object):
    '''Abstract base class for authentication.'''
    def __init__(self, settings):
        self.settings = settings
        # TODO: Replace "enable_gallery_mode" in configs
        self.disable_login = settings.get('disable_login') == 'true'

    def set_auth_cookie_and_redirect(self, user_id, location, request,
                                     headers=None):
        '''Stores the user_id in a cookie, for subsequent requests.'''
        if self.disable_login:  return
        if not headers:
            headers  = remember(request, user_id)
        else:
            headers += remember(request, user_id)
        # May also set max_age above. (pyramid.authentication, line 272)
        return HTTPFound(location=location, headers=headers)

    def authenticate(self, user, password):
        '''Should return the user object or None if the credentials are wrong.
        '''
        raise NotImplementedError()


class CasAuthenticator(BaseAuthenticator):
    def __init__(self, settings):
        super(CasAuthenticator, self).__init__(settings)
        self.connection_settings = dict(
            host=settings['CAS.host'],
            timeout=settings.get('CAS.timeout', 30),
        )
        # TODO: Mark this setting as required in development.ini-dist
        self.service = settings.get('scheme_domain_port')
        if not self.service:
            raise RuntimeError('You are missing the "scheme_domain_port" ' \
                               'setting in the .ini file.')

    def authenticate(self, user, password):
        with HTTPConnection(*self.connection_settings) as c:
            c.set_debuglevel(1)  # TODO: Remove printing
            c.request(method='POST', url='login', body=urlencode(dict(
                user=user, password=password,
            )))
            r = c.getresponse()
        print 'RESPONSE'
        print r.status, r.reason, r.getheaders(), r.read()
        # TODO: Instantiate the user object and return it
        return True

