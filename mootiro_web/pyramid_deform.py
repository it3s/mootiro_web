#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Functions to set up and more easily use Deform with Pyramid.'''

from __future__ import unicode_literals  # unicode by default

from pkg_resources import resource_filename
import deform as d
from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_request
from .user import _


def translator(term):
    return get_localizer(get_current_request()).translate(term)


def setup(deform_template_dirs):
    '''Add our deform templates and set deform up for i18n.
    Example:

        setup(['mootiro_form:fieldtypes/templates', 'deform:templates'])
    '''
    dirs = [resource_filename(*dir.split(':')) for dir in deform_template_dirs]
    d.Form.set_zpt_renderer(dirs, translator=translator)


def get_button(text=_('Submit')):
    '''Gets a string and generates a Deform button while setting its
    `name` attribute and capitalizing the label.
    '''
    return d.Button(title=translator(text).capitalize(),
                    name=filter(unicode.isalpha, text.lower()))


def make_form(form_schema, f_template='form', i_template='mapping_item',
              *args, **kwargs):
    form = d.Form(form_schema, *args, **kwargs)
    class F(d.widget.FormWidget):
        template = f_template
        item_template = i_template
    form.set_widgets({'':F()})
    return form
