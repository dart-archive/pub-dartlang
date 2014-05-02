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
    """The handler for /api/packages/*."""

    @handlers.api(2)
    def index(self, page=1):
        """Retrieve a paginated list of uploaded packages.

        Arguments:
          page: The page of packages to get. Each page contains 50 packages.
        """
        pager = QueryPager(int(page), "/api/packages?page=%d",
                           Package.all().order('-updated'),
                           per_page=100)
        return json.dumps({
            "packages": [package.as_dict() for package in pager.get_items()],
            "prev_url": pager.prev_url,
            "next_url": pager.next_url,
            "pages": pager.page_count
        })

    @handlers.api(2)
    def show(self, id):
        """Retrieve the page describing a specific package."""
        return json.dumps(handlers.request().package.as_dict(full=True))
