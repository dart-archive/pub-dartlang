# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import os

import cherrypy

from handlers import cloud_storage
import handlers

class Root(object):
    """The handler for /*."""

    def index(self):
        """Retrieves the front page of the package server."""
        return handlers.render('index')

    def site_map(self):
        """Retrieves a map of the site."""
        return handlers.render('site_map', layout={'title': 'Site Map'})

    def serve(self, filename):
        """Serves a cloud storage file for the development server."""

        if handlers.is_production(): return handlers.http_error(404)

        cherrypy.response.headers['Content-Type'] = 'application/octet-stream'
        cherrypy.response.headers['Content-Disposition'] = \
            'attachment; filename=%s' % os.path.basename(filename)

        try:
            with cloud_storage.open(filename) as f: return f.read()
        except KeyError, ExistenceError:
            handlers.http_error(404)
