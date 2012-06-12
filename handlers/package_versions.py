# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import cherrypy
import routes
from google.appengine.ext import db
from google.appengine.api import users

import handlers
from models.package import Package
from models.package_version import PackageVersion

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

    @handlers.handle_validation_errors
    def create(self, package_id, version, file):
        """Create a package version.

        If the user doesn't own the package, this will return a 403 error. If
        the package already has a version with this number, or if the version is
        invalid, this will redirect to the new version form.
        """

        package = handlers.request().package
        if not package.owner == users.get_current_user():
            handlers.http_error(
                403, "You don't own package '%s'" % package.name)

        failure_url = '/packages/%s/versions/new' % package.name
        if package.has_version(version):
            handlers.flash('Package "%s" already has version "%s".' %
                           (package.name, version))
            raise cherrypy.HTTPRedirect(failure_url)

        if not file.file:
            handlers.flash('No package uploaded.')
            raise cherrypy.HTTPRedirect(failure_url)

        PackageVersion(
            version = version,
            package = package,
            contents = db.Blob(file.file.read())).put()

        handlers.flash('%s %s created successfully.' % (package.name, version))
        raise cherrypy.HTTPRedirect(
            '/packages/%s/versions/%s' % (package.name, version))

    def show(self, package_id, id, format):
        """Retrieve the page describing a package version.

        Depending on the format, this could be a user-readable webpage (.html),
        a machine-readable JSON document (.json), or a download of the actual
        package blob (.tar.gz).
        """

        # The built-in format parsing has trouble with versions since they
        # contain periods, so we have to undo it and apply our own.
        id = '%s.%s' % (id, format)
        if id.endswith('.tar.gz'):
            id = id[0:-len('.tar.gz')]
            version = handlers.request().package_version(id)
            cherrypy.response.headers['Content-Type'] = \
                'application/octet-stream';
            cherrypy.response.headers['Content-Disposition'] = \
                'attachment; filename=%s-%s.tar.gz' % (package_id, id)
            return version.contents
        else:
            handlers.http_error(404)
