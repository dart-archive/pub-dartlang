# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import json

import cherrypy
from google.appengine.api import users

import handlers
import sys
import models
from models.package import Package
from models.private_key import PrivateKey

from google.appengine.api import files

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
    def create(self, file):
        """Create a new package.

        This creates both the package metadata and a single package version.

        If the user isn't logged in with admin privileges, this will return a
        403. If a package with the given name already exists, this will redirect
        to /packages/new.

        Arguments:
          file: The package archive.
        """

        if not users.is_current_user_admin():
            handlers.http_error(403, "Only admins may create packages.")

        package, version = Package.from_archive(file.file)

        if Package.exists(package.name):
            handlers.flash('A package named "%s" already exists.' %
                           package.name)
            raise cherrypy.HTTPRedirect('/packages/new')

        package.latest_version = version
        with models.transaction():
            package.put()
            version.put()
        handlers.flash('Package %s %s uploaded successfully.' %
                       (package.name, version.version))
        raise cherrypy.HTTPRedirect('/packages/%s' % package.name)

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

    def upload(self, file, key, acl=None, policy=None, signature=None,
               success_action_redirect=None, **kwargs):
        """A development-only action for uploading a package archive.

        In production, package archives are uploaded directly to cloud storage,
        using a signed form for authentication. The signed form doesn't work for
        the development server, since it uses a local database in place of cloud
        storage, so this action emulates it by manually saving the file to the
        development database.
        """

        if handlers.production(): raise handlers.http_error(404)
        if PrivateKey.sign(policy) != signature: raise handlers.http_error(403)

        write_path = files.gs.create('/gs/' + key, acl=acl)
        with files.open(write_path, 'a') as f:
            f.write(file.file.read())
        files.finalize(write_path)

        if success_action_redirect:
            raise cherrypy.HTTPRedirect(success_action_redirect)
        cherrypy.response.status = 204
        return ""

    def show(self, id, format='html'):
        """Retrieve the page describing a specific package."""
        if format == 'json':
            package = handlers.request().package
            cherrypy.response.headers['Content-Type'] = 'application/json'
            versions = [str(version.version) for version in package.version_set]
            return json.dumps({
                "name": package.name,
                "owner": package.owner.email(),
                "versions": versions
            })
        elif format == 'html':
            package = handlers.request().package
            version_count = package.version_set.count()
            return handlers.render(
                "packages/show", package=package,
                versions=package.version_set.order('-sort_order').fetch(10),
                version_count=version_count,
                show_versions_link=version_count > 10,
                is_uploader=package.owner == users.get_current_user())
        else:
            raise handlers.http_error(404)
