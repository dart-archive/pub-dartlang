# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import json

import cherrypy
from google.appengine.api import users

import handlers
import sys
from models.package import Package

class Packages(object):
    """The handler for /packages/*.

    This handler is in charge of packages (but not package versions, which are
    the responsibility of the PackageVersions class).
    """

    def index(self, page = 1):
        """Retrieve a paginated list of uploaded packages.

        Arguments:
          page: The page of packages to get. Each page contains 10 packages.
        """
        offset = (page - 1) * 10
        packages = Package.all().order('-updated').fetch(10, offset)
        return handlers.render("packages/index", packages=packages)

    @handlers.handle_validation_errors
    def create(self, name = None):
        """Create a new package.

        This only creates the package metadata; it doesn't handle uploading any
        package versions.

        If the user isn't logged in with admin privileges, this will return a
        403. If a package with the given name already exists, this will redirect
        to /packages/new.

        Arguments:
          name: The name of the package to create.
        """

        if not users.is_current_user_admin():
            handlers.http_error(403, "Only admins may create packages.")

        if Package.exists(name):
            handlers.flash('A package named "%s" already exists.' % name)
            raise cherrypy.HTTPRedirect('/packages/new')

        Package(name = name).put()
        handlers.flash('Package "%s" created successfully.' % name)
        # TODO(nweiz): redirect to actual package page
        raise cherrypy.HTTPRedirect('/packages')

    def new(self):
        """Retrieve the form for creating a package.

        If the user isn't logged in, this presents a login screen. If they are
        logged in but don't have admin priviliges, this redirects to /packages/.
        """
        if not users.get_current_user():
            raise cherrypy.HTTPRedirect(
                users.create_login_url(cherrypy.url()))
        elif not users.is_current_user_admin():
            handlers.flash('Currently only admins may create packages.')
            raise cherrypy.HTTPRedirect('/packages')

        return handlers.render("packages/new")

    def show(self, id, format='html'):
        """Retrieve the page describing a specific package."""
        if format == 'json':
            package = handlers.request().package
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return json.dumps({
                "name": package.name,
                "owner": package.owner.email(),
                "versions": [version.version for version in package.version_set]
            })
        elif format is 'html':
            package = handlers.request().package
            return handlers.render(
                "packages/show", package = package,
                versions = package.version_set.get(),
                is_owner = package.owner == users.get_current_user())
        else:
            raise handlers.http_error(404)
