# -*- coding: utf-8 -*-

'''Forms and views for authentication and user information editing.'''

from __future__ import unicode_literals  # unicode by default

try:
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree
import colander as c
from urllib import urlencode, urlopen
from turbomail import Message
from pyramid_handlers import action
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import get_locale_name
from pyramid.request import add_global_response_headers
from pyramid.security import remember, forget
from . import BaseView, _, authenticated
from ..pyramid_deform import make_form, get_button, d
from .models.user import User, sas
# , Form, FormCategory, SlugIdentification, \
#     EmailValidationKey, sas
from .schemas import create_user_schema, create_edit_user_schema, \
     create_edit_user_schema_without_mail_validation, \
     SendMailSchema, PasswordSchema, UserLoginSchema, ValidationKeySchema
from . import create_locale_cookie


user_login_schema = UserLoginSchema()
send_mail_schema = SendMailSchema()
password_schema = PasswordSchema()
validation_key_schema = ValidationKeySchema()


def send_mail_form(button=_('Send'), action=""):
    return d.Form(send_mail_schema, buttons=(get_button(button),),
                  action=action, formid='sendmailform')


def password_form(button=_('Change password'), action="", f_template="form"):
    return make_form(password_schema, f_template=f_template,
                     action=action, formid='passwordform',
                     buttons=(get_button(button) if button else None,))


def validation_key_form(button=_('Send'), action=""):
    return d.Form(validation_key_schema, buttons=(get_button(button),),
                  action=action, formid='validationkeyform')


def user_login_form(button=_('Log in'), action="", referrer="",
                    validator=None):
    if validator:  # TODO Rollback
        schema = UserLoginSchema(validator=validator)
    else:
        schema = user_login_schema
    return d.Form(schema, action=action,
                  buttons=(get_button(button),), formid='userform')


def logout_now(request):
    headers = forget(request)
    add_global_response_headers(request, headers)
    request.user = None


MSG_LST = [  # This separates translation msgs from line breaks
    _("Hello, {0}, welcome to MootiroForm!"),
    "\n",
    _("To get started using our tool, you have to activate your account:"),
    "\n",
    _("Visit this link,"),
    "{1}",
    "\n",
    _("or use this key: {2}"),
    _("on {3}."),
    "\n",
    _("If you have any questions or feedback, please contact us on"),
    "{4}\n",
    _("Mootiro team."),
]


class BaseAuthenticator(BaseView):
    '''Abstract base view for authentication.'''
    def set_auth_cookie_and_redirect(self, user_id, location=None,
                                     headers=None):
        '''Stores the user_id in a cookie, for subsequent requests.'''
        settings = self.request.registry.settings
        # TODO: Replace "enable_gallery_mode" in configs
        if settings.get('disable_login') == 'true':  return
        if not location:
            location = self.url('root')
        if not headers:
            headers  = remember(self.request, user_id)
        else:
            headers += remember(self.request, user_id)
        # May also set max_age above. (pyramid.authentication, line 272)
        return HTTPFound(location=location, headers=headers)


class CasView(BaseAuthenticator):
    '''An authentication view that delegates to a CAS server
    (Central Authentication Service).
    '''
    @staticmethod
    def add_routes(config, prefix='user/'):
        handler = config.add_handler
        handler('user', prefix + '{action}',
                handler='mootiro_web.user.views:CasView')

    @action(name='login', request_method='GET')
    def login_form(self):
        '''Redirects to the CAS login page if there is no logged user.'''
        settings = self.request.registry.settings
        if self.request.user:
            return HTTPFound(location='/')
        else:
            service = self.url('user', action='verify')
            return HTTPFound(location='http://' + settings['CAS.host'] + \
                '/login?' + urlencode(dict(service=service)))

    def _verify_cas2(self, ticket):
        """Verifies a CAS 2.0+ XML-based authentication ticket
        against the server.
        Returns username on success and None on failure.
        Code 'inspired' by http://code.google.com/p/django-cas/source/browse/django_cas/backends.py
        """
        params = {'ticket' : ticket,
                  'service': 'http://localhost:6543/user/verify',
                  # self.url('user', action='verify'),
        }
        page = urlopen('http://' + self.request.registry.settings['CAS.host'] \
            + '/proxyValidate?' + urlencode(params))
        try:
            response = page.read()
            tree = ElementTree.fromstring(response)
            if tree[0].tag.endswith('authenticationSuccess'):
                return tree[0][0].text
            else:
                return None
        finally:
            page.close()

    @action(request_method='GET')
    def verify(self):
        '''The CAS server redirects back to this view like this:
        http://localhost:6543/user/verify?ticket=ST-2-sG2bwsfXA5dAR9fBoRKd-cas

        Here we verify the passed ticket against the CAS server.
        If the CAS server gives us a user name, we ensure the user exists
        in our database.
        '''
        ticket = self.request.GET['ticket']  # the unicode ticket
        email = self._verify_cas2(ticket)
        if not email:
            return self.login_form()
        user = sas.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email)
            sas.add(user)
            sas.flush()
        return self.set_auth_cookie_and_redirect(user.id)

    @action(request_method='POST')
    def logout(self):
        '''Creates HTTP headers that cause the authentication cookie to be
        deleted and redirects to the CAS logout page.
        '''
        settings = self.request.registry.settings
        my_url = settings.get('scheme_domain_port') or \
            'http://' + self.request.environ.get('HTTP_HOST') + '/'
        return HTTPFound(headers=forget(self.request),
            location='http://' + self.request.registry.settings['CAS.host'] + \
            '/logout?' + urlencode(dict(url=my_url)))


class UserView(BaseAuthenticator):
    @staticmethod
    def add_routes(config, prefix='user/'):
        '''Configures URLs in this application.'''
        handler = config.add_handler
        config.add_static_view('user_static', 'mootiro_web.user:static')
        # handler('root', '',
        #         handler='mootiro_web.user.views:UserView.login', action='root')
        handler('user', prefix + '{action}',
                handler='mootiro_web.user.views:UserView')
        handler('reset_password', prefix + '{action}/{slug}',
                handler='mootiro_web.user.views:UserView')
        handler('email_validation', 'email_validation/{action}',
                handler='mootiro_web.user.views:UserView')
        handler('email_validator', 'email_validation/{action}/{key}',
                handler='mootiro_web.user.views:UserView')


    EDIT_TITLE = _('My account')
    LOGIN_TITLE = _('Login')
    CREATE_TITLE = _('Create an account')
    PASSWORD_TITLE = _('Change password')
    PASSWORD_SET_TITLE = _('You have successfully created a new password.')
    VALIDATION_TITLE = _('Email validation')

    def _create_user_form(self, button=_('Submit'), add_terms=False,
                          action=""):
        '''Apparently, Deform forms must be instantiated for every request.'''
        user_schema = create_user_schema(add_terms,
                                         self.request.registry.settings)
        return make_form(user_schema, f_template='form_required_explanation',
                         buttons=(get_button(button),),
                         action=action, formid='createuserform')

    @action(name='new', renderer='user_edit.genshi', request_method='GET')
    def new_user_form(self):
        '''Displays the form to create a new user.'''
        if self.request.user:
            return HTTPFound(location='/')
        add_terms = \
            self.request.registry.settings.get('terms_of_service', False)
        return dict(pagetitle=self.tr(self.CREATE_TITLE),
            user_form=self._create_user_form(_('Sign up'), add_terms=add_terms,
                action=self.url('user', action='new')).render(),
        )

    @action(name='new', renderer='user_edit.genshi', request_method='POST')
    def save_new_user(self):
        '''Creates a new User from POSTed data and sets the locale cookie
        coherent to the language the user selected if it validates;
        else redisplays the form with the error messages.
        '''
        settings = self.request.registry.settings
        # Disable user functionality when in gallery mode
        if settings.get('disable_login') == 'true':
            return

        controls = self.request.params.items()
        add_terms = \
            self.request.registry.settings.get('terms_of_service', False)
        try:
            appstruct = self._create_user_form(_('Sign up'),
                add_terms=add_terms,
                action=self.url('user', action='new')).validate(controls)
        except d.ValidationFailure as e:
            # print(e.args, e.cstruct, e.error, e.field, e.message)
            return dict(pagetitle=self.tr(self.CREATE_TITLE),
                        user_form=e.render())
        # Form validation passes, so create a User in the database.
        appstruct.pop('terms_of_service', 'not found')
        u = User(**appstruct)
        sas.add(u)
        sas.flush()

        # Set locale_cookie to the language the user selected and redirect to
        # the 'message' action (below). This is necessary to make the locale
        # cookie work for the next page and the validation email
        headers = self._set_locale_cookie()

        return HTTPFound(location=self.url('email_validation',
            action='message', _query=dict(user_id=u.id)), headers=headers)

    def terms(self):
        '''Renders the terms of service.'''
        locale_name = get_locale_name(self.request)
        if locale_name == 'en':
            return HTTPFound(location='http://mootiro.org/form/en/terms')
        elif locale_name == 'pt_BR':
            return HTTPFound(location='http://mootiro.org/form/pt-br/termos')
        else:
            return HTTPFound(location='/')

    @action(name='message', renderer='email_validation.genshi')
    def email_validation_message(self):
        '''Sends the validation mail to the user.'''
        # Fetches the user from the db via the url parameter passed in from the
        # action above
        user_id = self.request.params['user_id']
        user = sas.query(User).filter(User.id == user_id).one()
        # creates the evk and adds it to the db
        evk = EmailValidationKey(user)
        sas.add(evk)
        # Sends the email verification using TurboMail
        self._send_email_validation(user, evk)
        return dict(email_sent=True)

    def _send_email_validation(self, user, evk):
        sender = self.request.registry.settings.get('mail.message.author','sender@example.org')
        recipient = user.email
        subject = _("MootiroForm - Email Validation")
        link = self.url('email_validator', action="validator", key=evk.key)

        message = '\n'.join([self.tr(m) for m in MSG_LST]) \
                .format(user.nickname, link, evk.key,
                    self.url('email_validation', action="validate_key"),
                    self.url('contact'))
        msg = Message(sender, recipient, self.tr(subject))
        #msg = Message(recipient, self.tr(subject))
        msg.plain = message
        msg.send()

    def _set_locale_cookie(self):
        '''Set locale directly for the current request and the locale_cookie'''
        locale = self.request.POST['default_locale']
        settings = self.request.registry.settings
        return create_locale_cookie(locale, settings)

    def _edit_user_form(self, button=_('Submit'), mail_validation=True):
        '''Apparently, Deform forms must be instantiated for every request.'''
        if mail_validation:
            edit_user_schema = create_edit_user_schema \
                (self.request.registry.settings, self.tr)
        else:
            edit_user_schema = create_edit_user_schema_without_mail_validation \
                                    (self.request.registry.settings, self.tr)
        return make_form(edit_user_schema, f_template='edit_profile',
                         buttons=(get_button(button),),
                         formid='edituserform')

    @action(name='current', renderer='user_edit.genshi', request_method='GET')
    @authenticated
    def edit_user_form(self):
        '''Displays the form to edit the current user profile.'''
        user = self.request.user
        return dict(pagetitle=self.tr(self.EDIT_TITLE),
                user_form=self._edit_user_form() \
                    .render(self.model_to_dict(user, ('nickname', 'real_name', \
                    'email', 'default_locale'))))

    @action(name='current', renderer='user_edit.genshi', request_method='POST')
    @authenticated
    def update_user(self):
        '''Saves the user profile from POSTed data if it validates;
        else redisplays the form with the error messages.
        '''
        settings = self.request.registry.settings
        # Disable user functionality when in gallery mode
        if settings.get('disable_login') == 'true':
            return

        controls = self.request.POST.items()
        # If User does not change email, do not validate this field
        email = self.request.user.email
        if email == self.request.POST['email']:
            uf = self._edit_user_form(mail_validation=False)
        else:
            uf = self._edit_user_form()
        # Validate the instantiated form against the controls
        try:
            appstruct = uf.validate(controls)
        except d.ValidationFailure as e:
            # print(e.args, e.cstruct, e.error, e.field, e.message)
            return dict(pagetitle=self.tr(self.EDIT_TITLE),
                        user_form = e.render())
        # Form validation passes, so save the User in the database.
        user = self.request.user
        self.dict_to_model(appstruct, user) # update user
        sas.flush()
        # And set the language cookie, so the user browses directly with the
        # selected language
        headers = self._set_locale_cookie()
        return self.set_auth_cookie_and_redirect \
                    (user.id, self.url('root'), headers=headers)

    @action(name='edit_password', renderer='edit_password.genshi',
            request_method ='GET')
    @authenticated
    def show_password_form(self):
        '''Displays the form to edit the user's password.'''
        return dict(password_form=password_form(
                                   f_template='form_without_buttons').render())

    @action(name='edit_password', renderer='json',
            request_method = 'POST')
    @authenticated
    def update_password(self):
        '''Updates the user's password and redirects back to the edit profile
        view.
        '''
        # validate instatiated form against the controls
        controls = self.request.POST.items()
        try:
            appstruct = password_form(f_template='form_without_buttons') \
                                                            .validate(controls)
        except d.ValidationFailure as e:
            self.request.override_renderer = 'edit_password.genshi'
            return dict(password_form=e.render())
        # Form validation passes, so update the password in the database.
        user = self.request.user
        self.dict_to_model(appstruct, user) # save password
        sas.flush()
        return dict(changed=True)

    @action(name='login', renderer='user_login.genshi', request_method='GET')
    def login_form(self):
        '''Shows the login page if there is no logged user.'''
        if self.request.user:
            return HTTPFound(location='/')
        else:
            return self._login_dict()

    def _login_dict(self, posted={}, errors={}):
        '''The seemingly simple login page has some boilerplate in its
        number of variables; this method makes that easier.
        '''
        referrer = self.request.GET.get('ref', self.url('root'))
        action = self.url('user', action='login', _query=[('ref', referrer)])
        return dict(
            pagetitle=self.tr(self.LOGIN_TITLE),
            action=action,
            hide_login_box=False,
            error_form=errors.get('general', None),
            error_email=errors.get('login_email'),
            error_password=errors.get('login_pass'),
            login_email=posted.get('login_email'),
            login_password=None,  # Never transmit any password back to client.
        )

    @action(name='login', renderer='email_validation.genshi',
            request_method='POST')
    def login(self):
        # Disable user functionality when in gallery mode
        settings = self.request.registry.settings
        if settings.get('disable_login') == 'true':
            raise RuntimeError('Login attempted, but in gallery mode :p')

        # Validate the email and password using only colander
        posted = {
            'login_email': self.request.POST.get('login_email', ''),
            'login_pass' : self.request.POST.get('login_pass', ''),
        }
        try:
            posted = user_login_schema.deserialize(posted)
        except c.Invalid as e:
            self.request.override_renderer = 'user_login.genshi'
            return self._login_dict(posted, errors=e.asdict())

        u = User.get_by_credentials(posted['login_email'],
                                    posted['login_pass'])
        if u:
            if u.is_email_validated:
                # User is good; just set locale cookie
                locale = u.default_locale
                settings = self.request.registry.settings
                headers = create_locale_cookie(locale, settings)
                # The final destination URL may be passed in as a URL parameter
                referrer = self.request.GET.get('ref', self.url('root'))
                return self.set_auth_cookie_and_redirect \
                    (u.id, referrer, headers=headers)
            else:
                # User is awaiting email validation
                return dict(email_sent=True)
        else:
            # Wrong user or password. Re-display the form, with warnings.
            self.request.override_renderer = 'user_login.genshi'
            return self._login_dict(posted, errors=dict(
                general=_('Wrong email or password. Please try again.'),
            ))

    @action(request_method='POST')
    def logout(self):
        '''Creates HTTP headers that cause the authentication cookie to be
        deleted and redirects to the front page.
        '''
        headers = forget(self.request)
        return HTTPFound(location=self.url('root'), headers=headers)

    @action(name='send_recover_mail', renderer='recover_password.genshi',
            request_method='GET')
    def forgotten_password(self):
        '''Display the form to send an email to the user to enable him to
        change his password.
        '''
        if self.request.user:
            return HTTPFound(location='/')
        return dict(pagetitle=self.tr(self.PASSWORD_TITLE),
                    email_form=send_mail_form().render())

    @action(name='send_recover_mail', renderer='recover_password.genshi',
            request_method='POST')
    def send_recover_mail(self):
        '''Creates a slug to identify the user and sends a mail to the given
        address to enable resetting the password.
        '''
        controls = self.request.POST.items()
        try:
            appstruct = send_mail_form().validate(controls)
        except d.ValidationFailure as e:
            return dict(pagetitle=self.tr(self.PASSWORD_TITLE),
                email_form=e.render())
        '''Form validation passes, so create a slug and the url and send an
        email to the user to enable him to reset his password.'''
        email = appstruct['email']
        user = sas.query(User).filter(User.email == email).first()
        # Create the slug to identify the user and save it in the db
        si = SlugIdentification.create_unique_slug(user)
        sas.add(si)
        sas.flush()

        # Create the url and send it to the user
        slug = si.user_slug
        password_link = self.url('reset_password', action='recover', slug=slug)

        sender = self.request.registry.settings.get('mail.message.author','sender@example.org')
        recipient = email
        subject = _("MootiroForm - Change Password")
        message = _("To set a new password please click on the link: ")

        msg = Message(sender, recipient, self.tr(subject))
        msg.plain = self.tr(message) + password_link
        msg.send()
        return dict(pagetitle=self.tr(self.PASSWORD_TITLE), email_form=None)

    @action(name='recover', renderer='enter_new_password.genshi',
            request_method='GET')
    def receive_password(self):
        slug = self.request.matchdict['slug']
        si = sas.query(SlugIdentification) \
                .filter(SlugIdentification.user_slug == slug).first()
        if si:
            # render form if password was not yet resetted
            return dict(pagetitle=self.tr(self.PASSWORD_TITLE),
                        password_form=password_form().render(), invalid=False, \
                        resetted=False)
        else:
            # render 'Password was already resetted'
            url = self.url('user', action='send_recover_mail')
            return dict(pagetitle=self.tr(self.PASSWORD_TITLE),
                        password_form=None, invalid=True, \
                        resetted=False, link=url)

    @action(name='recover', renderer='enter_new_password.genshi',
            request_method='POST')
    def alter_password(self):
        # fetch user via slug
        slug = self.request.matchdict['slug']
        try:
            si = sas.query(SlugIdentification) \
                .filter(SlugIdentification.user_slug == slug).one()
        except:
            url = self.url('user', action='send_recover_mail')
            return dict(pagetitle=self.tr(self.PASSWORD_TITLE),
                        password_form=None,
                        invalid=True, resetted=False, link=url)
        user = si.user
        # validate instatiated form against the controls
        controls = self.request.POST.items()
        try:
            appstruct = password_form().validate(controls)
        except d.ValidationFailure as e:
            return dict(pagetitle=self.tr(self.PASSWORD_TITLE),
                        password_form=e.render(),
                        invalid=False, resetted=False)
        # and delete the slug afterwards so the email link can only be used once
        sas.delete(si)
        # save new password in the database
        new_password = appstruct['password']
        user.password = new_password
        return dict(pagetitle=self.tr(self.PASSWORD_SET_TITLE),
                    password_form=None,
                    resetted=True, invalid=False)

    @action(name='delete', request_method='POST', renderer='user_delete.genshi')
    def delete_user(self):
        ''' This view deletes the user and all data associated with her.
        Plus, it weeps a tear for the loss of the user.
        '''
        sas.delete(self.request.user)
        sas.flush()
        logout_now(self.request)
        return dict(pagetitle=self.tr("Your profile was deleted"),)

    @action(name='validator', renderer='email_validation.genshi')
    def validator(self):
        key = self.request.matchdict['key']
        evk = sas.query(EmailValidationKey) \
                .filter(EmailValidationKey.key == key).first()

        rdict = dict(key=key)
        if not evk:
            rdict["invalid_key"] = True
        else:
            self._validate(evk)
            rdict["validated"] = True

        return rdict

    def _validate(self, evk):
        if not evk: return False

        user = evk.user
        user.is_email_validated = True
        sas.delete(evk)
        return True

    @action(name='validate_key', renderer='email_validation.genshi', request_method='GET')
    def validate_key_form(self):
        '''Display the form to input the validation key.'''
        return dict(pagetitle=self.tr(self.VALIDATION_TITLE),
                key_form=validation_key_form(action=self
                    .url('email_validation', action="validate_key")).render())

    @action(name='validate_key',
            renderer='email_validation.genshi', request_method='POST')
    def validate_key(self):
        post = self.request.POST
        key = post.get('key')

        rdict = dict()

        controls = post.items()
        try:
            validation_key_form( \
                action=self.url('email_validation', action="validate_key")) \
                        .validate(controls)
        except d.ValidationFailure as e:
            return dict(pagetitle=self.tr(self.VALIDATION_TITLE),
                    key_form=e.render())

        evk = sas.query(EmailValidationKey).filter( \
                    EmailValidationKey.key == key).first()
        self._validate(evk)
        rdict["validated"] = True

        return rdict

    @action(name='resend', renderer='email_validation.genshi',
            request_method='GET')
    def resend_email_form(self):
        '''Display the forms to resend email validation key.'''
        return dict(pagetitle=self.tr(self.VALIDATION_TITLE),
                    email_form=send_mail_form(action=self
                        .url('email_validation', action="resend")).render())

    @action(name='resend', renderer='email_validation.genshi',
            request_method='POST')
    def resend_email(self):
        post = self.request.POST
        email = post.get('email')

        rdict = dict()

        controls = post.items()
        try:
            send_mail_form( \
                action=self.url('email_validation', action="resend")) \
                    .validate(controls)
        except d.ValidationFailure as e:
            return dict(pagetitle=self.tr(self.VALIDATION_TITLE),
                        email_form=e.render())

        user = sas.query(User).filter(User.email == email).first()
        evk = sas.query(EmailValidationKey) \
            .filter(EmailValidationKey.user == user).first()

        if not evk:
            rdict['invalid_email'] = True
            rdict.update(**self.resend_email_form())
        else:
            self._send_email_validation(user, evk)
            rdict['email_sent'] = True

        return rdict
