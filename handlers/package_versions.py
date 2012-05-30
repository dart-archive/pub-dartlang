# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import cherrypy
import routes
from google.appengine.api import users

import handlers
from models.package import Package

class PackageVersions(object):
    """The handler for packages/*/versions/*.

    This handler is in charge of individual versions of packages.
    """

    def new(self, package_id):
        """Retrieve the page for uploading a package version.

        If the user isn't logged in, this presents a login screen. If they are
        logged in but don't own the package, this redirects to the page for the
        package.
        """
        user = users.get_current_user()
        package = handlers.request().package
        if not user:
            raise cherrypy.HTTPRedirect(
                users.create_login_url(cherrypy.url()))
        elif not package.owner == user:
            handlers.flash("You don't down package '%s'" % package.name)
            raise cherrypy.HTTPRedirect('/packages/%s' % package.name)

        return handlers.render("packages/versions/new",
                               action=handlers.request().url(action='create'),
                               package=package)

