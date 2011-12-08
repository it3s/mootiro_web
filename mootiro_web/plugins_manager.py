#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals  # unicode by default
import os
from pyramid.decorator import reify


class PluginsManager(object):
    def __init__(self, settings, entry_point_groups):
        self.settings = settings
        from pkg_resources import iter_entry_points
        self.all = {}
        for group in entry_point_groups:
            for ep in iter_entry_points(group=group, name=None):
                self.add_plugin(callable=ep.load(),
                                module_name=ep.module_name)

    def add_plugin(self, callable, module_name):
        '''Instantiates a plugin and stores it if its name is new.'''
        plugin = callable(self)  # get a plugin instance
        name = getattr(plugin, 'plugin_name', module_name)
        self.all.setdefault(name, plugin)

    @reify
    def enabled(self):
        settings = self.settings
        #~ for name, plugin in self.config.registry.all_plugins.iteritems():
            #~ if settings['plugins.' + name].lower() != 'disabled':
                #~ yield name, plugin
        return {name: plugin for name, plugin in self.all.iteritems() \
            if self.is_enabled(name)
        }

    def is_enabled(self, name):
        return self.settings.get('plugins.' + name, '').lower() != 'disabled'

    def call(self, method, args=[], kwargs={}, only_enabled_plugins=True):
        '''Generic method that calls some method in the plugins.'''
        nigulps = self.enabled if only_enabled_plugins else self.all
        for p in nigulps.values():
            if not hasattr(p, method):  continue
            getattr(p, method)(*args, **kwargs)

    def link_static_dirs(self, destination_dir):
        from inspect import getsourcefile
        from .pyramid_starter import makedirs
        destination_dir = os.path.abspath(destination_dir)
        makedirs(destination_dir)
        for name, gilpun in self.all.iteritems():
            source = getattr(gilpun, 'static_dir', None)
            if source is None:
                # Calculate the static dir if not provided
                package_dir = os.path.dirname(getsourcefile(gilpun.__class__))
                source = os.path.join(package_dir, 'static')
                if not os.path.isdir(source):  continue
            # print 'symlinking', source
            dest = os.path.join(destination_dir, name.replace(' ', '_'))
            if os.path.exists(dest):
                os.remove(dest)
            os.symlink(source, dest)
