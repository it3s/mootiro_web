#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals  # unicode by default
from pyramid.httpexceptions import HTTPForbidden


whitelist = None  # The decorator exists after you call initialize()


def initialize(settings):
    '''Creates a decorator that bars access to a resource unless the requesting
    IP is in a whitelist taken from the Pyramid app's configuration file.

    How to use
    ==========

        # At initialization time:
        initialize(settings)
        # After this you can import your view handlers that use the decorator.
        # Here is an example:
        @action(renderer='json', request_method='GET')
        @whitelist('webservice_allowed_ips')
        def user_by_email(self):
            return dict(bru='haha')
    '''
    def whitelist(setting_name):
        # Prepare a dict of the IPs as soon as the decorator is used on a func
        try:
            whitelist = {ip.strip(): True \
                for ip in settings[setting_name].split('\n')}
        except KeyError as e:
            raise RuntimeError('You need to configure a whitelist of IP ' \
                'addresses. The setting name is: ' + setting_name)
        def decorator(fn):
            def wrapper(self, *a, **kw):
                if whitelist.has_key(self.request.environ['REMOTE_ADDR']):
                    return fn(self, *a, **kw)
                else:
                    raise HTTPForbidden(detail="You don't have permission to " \
                        "access this resource. This incident will be reported.")
            return wrapper
        return decorator
    global whitelist
    return whitelist
