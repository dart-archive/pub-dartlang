# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import json

import cherrypy

import handlers

class Root(object):
    """The handler for /api/*."""

    @handlers.api(2)
    def index(self):
        """Retrieves the index of all entrypoints to the API."""
        return json.dumps({
            "packages_url": handlers.request().url(
                controller="api.packages", action="index") + "{/package}"
        })
