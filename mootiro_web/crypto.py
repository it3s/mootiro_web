#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals  # unicode by default

import os
import base64
import json

from Crypto.Cipher import AES
from Crypto.PublicKey import RSA

__all__ = ['load_rsa_key', 'encrypt', 'decrypt', 'encrypted']
__rsa_key = None


def load_rsa_key(filename):
    ''' Load a RSA key from 'filename'. '''
    # INFO: The public key can be used only to encrypt.
    with open(filename, 'r') as key_file:
        key_body = key_file.read()

    return RSA.importKey(key_body)


def encrypt(text, rsa_key):
    ''' Encrypt a string using AES and RSA.

    Uses AES with a random key to encrypt 'text' and than uses 'rsa_key' to
    encrypt the AES key. Returns the encrypted string and the encrypted key
    encoded as base64 in a json.
    '''
    content = text.encode('utf8')

    # The string must be a multiple of 16 in length.
    content_length = len(content)
    if content_length <= 16:
        missing = 16 - content_length
    else:
        missing = 16 - (content_length % 16)
    content = b'{}{}'.format(content, b'\x00' * missing)  # Append null chars.

    aes_key = os.urandom(32)  # Generate a random key.
    aes_mode = AES.MODE_CBC
    encryptor = AES.new(aes_key, aes_mode)

    encrypted_key = rsa_key.encrypt(aes_key, '')
    encrypted_content = encryptor.encrypt(content)

    # Using base64 we avoid encode issues.
    base64_key = base64.encodestring(encrypted_key[0])
    base64_content = base64.encodestring(encrypted_content)

    return json.dumps({'key': base64_key, 'content': base64_content})


def decrypt(encrypted_json, rsa_key):
    ''' Decrypt the 'encrypted_json' content encrypted using AES and RSA. '''
    d = json.loads(encrypted_json, encoding="utf8")

    encrypted_key = base64.decodestring(d['key'])
    encrypted_content = base64.decodestring(d['content'])

    aes_key = rsa_key.decrypt(encrypted_key)
    aes_mode = AES.MODE_CBC
    encryptor = AES.new(aes_key, aes_mode)

    content = encryptor.decrypt(encrypted_content)
    content = content.decode('utf8')
    content = content.rstrip(b'\x00')  # Remove all null chars appended.

    return content


def encrypted(func):
    ''' Decorator to encrypt strings. This decorator should be at the top of
    decorators list.

    How to use
    ==========

        # At initialization time:
        rsa_key = load_rsa_key('key_filename')
        initialize(rsa_key)
        # After this you can import your view handlers that use the decorator.
        # Here is an example:
        @encrypted
        @action(renderer='json', request_method='GET')
        def user_by_email(self):
            return dict(bru='haha')
    '''
    def wrapper(self, *a, **kw):
        global __rsa_key
        if not __rsa_key:
            raise RuntimeError('The mootiro_web.crypto module have to be '
                    'initialized before calling methods using the '
                    '"encrypted" decorator.')
        ret = func(self, *a, **kw)
        if not isinstance(ret, basestring):
            raise TypeError('The decorator "encrypted" expected a string '
                    'but the method "{}" returned a {}.'.format(
                        func.__name__, type(ret).__name__))
        return encrypt(ret, __rsa_key)

    return wrapper


def initialize(rsa_key):
    global __rsa_key
    __rsa_key = rsa_key  # Add RSA key to be used by decorator.

