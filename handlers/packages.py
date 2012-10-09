# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import json

import cherrypy
from google.appengine.api import users

import handlers
from handlers.pager import Pager
from models.package import Package

class Packages(object):
    """The handler for /packages/*.

    This handler is in charge of packages (but not package versions, which are
    the responsibility of the PackageVersions class).
    """

    def index(self, page=1):
        """Retrieve a paginated list of uploaded packages.

        Arguments:
          page: The page of packages to get. Each page contains 10 packages.
        """
        pager = Pager(
            int(page), "/packages?page=%d", Package.all().order('-updated'))
        title = 'All Packages'
        if page != 1: title = 'Page %s | %s' % (page, title)
        return handlers.render("packages/index",
                               packages=pager.get_items(),
                               pagination=pager.render_pagination(),
                               layout={'title': title})

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
            title = '%s %s' % (package.name, package.latest_version.version)
            return handlers.render(
                "packages/show", package=package,
                versions=package.version_set.order('-sort_order').fetch(10),
                version_count=version_count,
                show_versions_link=version_count > 10,
                is_uploader=package.owner == users.get_current_user(),
                layout={'title': title})
        else:
            raise handlers.http_error(404)
