# -*- coding: utf-8 -*-
'''Class used for checking if user provided email is a valid one'''

from __future__ import unicode_literals # unicode by default

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Unicode, Integer
from sqlalchemy.orm import relationship, backref
from . import Base, id_column, now_column
from .user import User
from mootiro_web.text import random_word


class EmailValidationKey (Base):
    '''Represents a temporary generated key for validating users against
    their alleged emails.
    '''
    __tablename__ = "email_validation_key"

    id = id_column(__tablename__)
    key = Column(Unicode(20), nullable=False, unique=True)
    generated_on = now_column()

    user_id = Column(Integer, ForeignKey('user.id'), index=True)
    user = relationship(User, backref=backref('email_validation_key',
                                              cascade='all'))

    def __init__(self, user):
        self.key = random_word(20)
        self.user = user

    def __repr__(self):
        return self.key or ''
