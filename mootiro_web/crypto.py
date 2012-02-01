#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
To create 2 files representing an RSA key pair:

    cd data
    ssh-keygen -t rsa -f crypto_key
    cd ..

Now you can use the library by:

    from mootiro_web.crypto import enable_crypto
    enable_crypto(config, 'data/crypto_key')
'''
from __future__ import unicode_literals  # unicode by default

import os
import base64
import json

try:
    from Crypto.Cipher import AES
    from Crypto.PublicKey import RSA
except ImportError:
    print("You need to get a pycrypto version >= 2.5. "
          'Try: easy_install -UZ pycrypto')
    raise

__all__ = ['load_rsa_key', 'encrypt', 'decrypt', 'enable_crypto']


def load_rsa_key(filename): #  pragma: no cover
    ''' Loads a RSA key from 'filename'. '''
    # INFO: The public key can be used only to encrypt.
    with open(filename, 'r') as key_file:
        key_body = key_file.read()

    return RSA.importKey(key_body)


def encrypt(text, rsa_key):
    ''' Encrypts a string using AES and RSA.

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
    ''' Decrypts the 'encrypted_json' content encrypted using AES and RSA. '''
    d = json.loads(encrypted_json, encoding='utf8')

    encrypted_key = base64.decodestring(d['key'])
    encrypted_content = base64.decodestring(d['content'])

    aes_key = rsa_key.decrypt(encrypted_key)
    aes_mode = AES.MODE_CBC
    encryptor = AES.new(aes_key, aes_mode)

    content = encryptor.decrypt(encrypted_content)
    content = content.rstrip(b'\x00')  # Remove all null chars appended.
    content = content.decode('utf8')

    return content


def enable_crypto(config, rsa_key_filename=None, rsa_key=None):
    ''' Enables this module to be possible encrypt Pyramid views. '''
    from zope.interface import implements
    from pyramid.renderers import get_renderer
    from pyramid.interfaces import ITemplateRenderer

    class CryptoRenderer(object):
        ''' Renderer to encrypt Pyramid views.

        How to use
        ==========

        # At initialization time:
        enable_crypto(config, rsa_key_filename)
        # You can append ".encrypted" to any renderer.
        # Here is an example:
        @action(renderer='json.encrypted', request_method='GET')
        def user_by_email(self):
            return dict(bru='haha')
        '''
        implements(ITemplateRenderer)

        name = '.encrypted'

        def __init__(self, rsa_key):
            self.rsa_key = rsa_key

        def __call__(self, value, system):
            request = system.get('request')
            if request is not None:
                response = request.response
                ct = response.content_type
                if ct == response.default_content_type:
                    response.content_type = 'application/json'

            # Get the original renderer
            orig_renderer_name = system['renderer_name'][:len(self.name) * -1]
            orig_renderer = get_renderer(orig_renderer_name)
            content = orig_renderer(value, system)

            return encrypt(content, self.rsa_key)

    rsa_key = rsa_key or load_rsa_key(rsa_key_filename)
    renderer = CryptoRenderer(rsa_key)
    config.add_renderer(renderer.name, lambda info: renderer)
