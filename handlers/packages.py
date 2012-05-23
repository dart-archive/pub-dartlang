# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import cherrypy
from google.appengine.api import users

import handlers
import sys
from models.package import Package

class Packages:
    def _index_get(self, page = 1):
        offset = (page - 1) * 10
        packages = Package.all().order('-updated').fetch(10, offset)
        return handlers.render("packages/index", packages = packages)
        raise cherrypy.HTTPRedirect("/")

    def _index_post(self, name = None):
        if not users.is_current_user_admin():
            raise cherrypy.HTTPError(403, "Only admins may create packages.")

        if not Package.create_unless_exists(name):
            handlers.flash('A package named "%s" already exists.' % name)
            raise cherrypy.HTTPRedirect('/packages/create')

        handlers.flash('Package "%s" created successfully.' % name)
        # TODO(nweiz): redirect to actual package page
        raise cherrypy.HTTPRedirect('/packages/')

    index = handlers.dispatch_by_method(
        GET  = _index_get,
        POST = _index_post)

    @cherrypy.expose
    def create(self):
        if not users.get_current_user():
            raise cherrypy.HTTPRedirect(
                users.create_login_url(cherrypy.url()))
        elif not users.is_current_user_admin():
            handlers.flash('Currently only admins may create packages.')
            raise cherrypy.HTTPRedirect('/packages/')

        return handlers.render("packages/create")
