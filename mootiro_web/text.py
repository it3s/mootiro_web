# -*- coding: utf-8 -*-
from __future__ import unicode_literals  # unicode by default

import random


def random_word(length, chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ' \
                              'abcdefghijklmnopqrstuvwxyz' \
                              '0123456789'):
    '''Returns a random string of some `length`.'''
    return ''.join((random.choice(chars) for i in xrange(length)))
