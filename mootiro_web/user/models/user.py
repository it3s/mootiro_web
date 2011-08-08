# -*- coding: utf-8 -*-
'''Auth/auth models: User, (more to come)'''

from __future__ import unicode_literals  # unicode by default

from hashlib import sha1
from sqlalchemy import Column
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.types import Unicode, Boolean
from . import Base, id_column, now_column
from . import sas


class User(Base):
    '''Represents a user of the application: someone who creates forms.
    *nickname* is a short name used for displaying in small spaces.
    *real_name* is supposed to be the real thing ;)
    *email* is what we really use for login.
    *password_hash* is used for password verification; we don't store the
    actual password for security reasons.
    *password* is a property so you can just set it and forget about the hash.
    This can also store phones and one address.
    '''
    __tablename__ = "user"

    LEN_PASSWORD = 32

    id = id_column(__tablename__)
    created = now_column()  # when was this user created
    changed = now_column()  # when did the user last update their data
    nickname = Column(Unicode(32), nullable=False, unique=True)
    real_name = Column(Unicode(255))
    email = Column(Unicode(255), nullable=False, unique=True)
    newsletter = Column(Boolean, default=False)  # wishes to receive news?
    is_email_validated = Column(Boolean, default=False)
    default_locale = Column(Unicode(5), default='en')

    password_hash = Column(Unicode(40), nullable=False, index=True)

    @classmethod
    def calc_hash(cls, password):
        '''Creates the password hash that is actually saved to the database.
        The returned hash is a unicode object containing a
        40 character long hexadecimal number.
        For this to work, a *salt* string must have been added to this class
        during configuration. (Yeah, monkeypatching.)
        This way the salt will be different for each
        installation (this is an open source app).
        '''
        return unicode(sha1(cls.salt + password).hexdigest())

    @property
    def password(self):
        '''Transient property, does not get persisted.'''
        return self.__dict__.get('_password')  # may return None

    @password.setter
    def password(self, password):
        self._password = password
        self.password_hash = User.calc_hash(password)

    @property
    def first_name(self):
        return self.real_name.split(' ')[0]

    def __repr__(self):
        return '[ {0}: {1} <{2}> ]'.format(self.id, self.nickname, self.email)

    def __unicode__(self):
        return self.nickname or ''

    @classmethod
    def get_by_credentials(cls, email, password):
        password_hash = cls.calc_hash(password)
        try:
            return sas.query(cls).filter(cls.email == email) \
                .filter(cls.password_hash == password_hash).one()
        except NoResultFound:
            return None

    def delete_user(self):
        sas.delete(self)
        sas.flush()
        return

    def all_categories_and_forms(self):
        ''' This function uses two backreferences in order to show us all the
        associated categories and forms. We use it to fill our forms list.
        '''
        all_data = dict()
        all_data['categories'] = list()
        # This exists so we can render the message for creating a form,
        # when the user has none
        if self.forms:
            all_data['forms_existence'] = True
            # If there are uncategorized forms, we insert them
            forms = [f.to_dict() for f in self.forms if f.category==None]

            if forms:
                all_data['categories'].append({
                         'category_desc': None,
                         'category_id':   "new",
                         'category_name': 'uncategorized',
                         'category_desc': None,
                         'category_position': None,
                         'forms': forms  })
        else:
            all_data['forms_existence'] = False

        # Now we insert the categorized forms
        all_data['categories'] += [category.to_dict() for category in self.categories]
        return all_data  # json.dumps(all_categories, indent=4)


''' FUTURE: We are probably not going to need
traditional User-Group-Permission security; instead:
Possibilidade de criação de grupos de usuários por um usuário, convidando
outro usuário a participar mediante confirmação, para o efeito de criar
formulários a serem respondidos por certos pesquisadores sem necessidade de
escolhê-los todas as vezes.

class Group(Base):
    __tablename__ = 'group'
    id = id_column(__tablename__)
    name = Column(Unicode(32), unique=True, nullable=False)
    description = Column(Unicode(255), nullable=False)
    created = now_column()
'''
