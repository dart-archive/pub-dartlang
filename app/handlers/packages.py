# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import json

import cherrypy
from google.appengine.api import users

import handlers
from handlers.pager import QueryPager
from models.package import Package

class Packages(object):
    """The handler for /packages/*.

    This handler is in charge of packages (but not package versions, which are
    the responsibility of the PackageVersions class).
    """

    @handlers.json_or_html_action
    def index(self, page=1, format='html'):
        """Retrieve a paginated list of uploaded packages.

        Arguments:
          page: The page of packages to get. Each page contains 10 packages.
        """
        if format == 'json':
            pager = QueryPager(int(page), "/packages.json?page=%d",
                               Package.all().order('-updated'),
                               per_page=50)
            return json.dumps({
                "packages": [
                    handlers.request().url(action='show', id=package.name)
                    for package in pager.get_items()
                ],
                "prev": pager.prev_url,
                "next": pager.next_url,
                "pages": pager.page_count
            })
        else:
            pager = QueryPager(int(page), "/packages?page=%d",
                               Package.all().order('-updated'))
            title = 'All Packages'
            if page != 1: title = 'Page %s | %s' % (page, title)
            return handlers.render("packages/index",
                                   packages=pager.get_items(),
                                   pagination=pager.render_pagination(),
                                   layout={'title': title})

    @handlers.json_or_html_action
    def show(self, id, format='html'):
        """Retrieve the page describing a specific package."""
        if format == 'json':
            package = handlers.request().package
            versions = [str(version.version) for version in package.version_set]
            return json.dumps({
                "name": package.name,
                "uploaders": [uploader.email() for uploader
                              in package.uploaders],
                "versions": versions
            })
        elif format == 'html':
            package = handlers.request().package
            version_count = package.version_set.count()

            title = package.name
            readme = None
            readme_filename = None
            changelog = None
            changelog_filename = None
            if package.latest_version:
                title = '%s %s' % (package.name, package.latest_version.version)

                readme_obj = package.latest_version.readme_obj
                if readme_obj:
                    readme = readme_obj.render()
                    readme_filename = readme_obj.filename

                changelog_obj = package.latest_version.changelog_obj
                if changelog_obj:
                    changelog = changelog_obj.render()
                    changelog_filename = changelog_obj.filename

            return handlers.render(
                "packages/show", package=package,
                versions=package.version_set.order('-sort_order').fetch(10),
                version_count=version_count,
                show_versions_link=version_count > 10,
                readme=readme,
                readme_filename=readme_filename,
                changelog=changelog,
                changelog_filename=changelog_filename,
                layout={'title': title})
        else:
            raise handlers.http_error(404)
