#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals  # unicode by default

import unittest

from Crypto.PublicKey import RSA
from pyramid import testing


class TestEncryptDecrypt(unittest.TestCase):
    def setUp(self):
        self.rsa_key = RSA.generate(1024)

    def test_encrypt_small_text(self):
        from mootiro_web.crypto import encrypt
        text = '   hi   '
        encrypted = encrypt(text, self.rsa_key)

    def test_encrypt_format(self):
        from mootiro_web.crypto import encrypt
        text = '   This is just a simple test   '
        encrypted = encrypt(text, self.rsa_key)
        self.assertIn('"content":', encrypted)
        self.assertIn('"key":', encrypted)

    def test_encrypt_n_decrypt(self):
        from mootiro_web.crypto import encrypt, decrypt
        text = '   This is just a simple test   '
        encrypted = encrypt(text, self.rsa_key)
        decrypted = decrypt(encrypted, self.rsa_key)
        self.assertEqual(decrypted, text)


class TestRenderer(unittest.TestCase):
    def setUp(self):
        self.rsa_key = RSA.generate(1024)
        self.config = testing.setUp()
        self.config.begin()

    def tearDown(self):
        self.config.end()

    def test_enable_crypto(self):
        from mootiro_web.crypto import enable_crypto
        enable_crypto(self.config, rsa_key=self.rsa_key)

    def test_render(self):
        from pyramid.renderers import render
        from mootiro_web.crypto import enable_crypto
        enable_crypto(self.config, rsa_key=self.rsa_key)
        result_normal = render('json', {'a': 1})
        result_encrypted = render('json.encrypted', {'a': 1})
        self.assertNotEqual(result_normal, result_encrypted)

    def test_decrypt(self):
        from pyramid.renderers import render
        from mootiro_web.crypto import enable_crypto, decrypt
        enable_crypto(self.config, rsa_key=self.rsa_key)
        result_normal = render('json', {'a': 1})
        result_encrypted = render('json.encrypted', {'a': 1})
        result_decrypted = decrypt(result_encrypted, self.rsa_key)
        self.assertEqual(result_normal, result_decrypted)

    def test_with_request_content_type_notset(self):
        from pyramid.renderers import render
        from mootiro_web.crypto import enable_crypto
        enable_crypto(self.config, rsa_key=self.rsa_key)
        request = testing.DummyRequest()
        render('json.encrypted', {'a': 1}, request)
        self.assertEqual(request.response.content_type, 'application/json')

    def test_with_request_content_type_set(self):
        from pyramid.renderers import render
        from mootiro_web.crypto import enable_crypto
        enable_crypto(self.config, rsa_key=self.rsa_key)
        request = testing.DummyRequest()
        request.response.content_type = 'text/mishmash'
        render('json.encrypted', {'a': 1}, request)
        self.assertEqual(request.response.content_type, 'text/mishmash')
