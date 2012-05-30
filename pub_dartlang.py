# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

"""The entrypoint for the pub.dartlang.org server.

In development, this should be run using the App Engine dev_appserver.py script.
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'third_party'))

import cherrypy
from google.appengine.ext.webapp.util import run_wsgi_app

from handlers.root import Root
from handlers.packages import Packages
from handlers.package_versions import PackageVersions

class Application(cherrypy.Application):
    """The pub.dartlang.org WSGI application."""

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(None, *args, **kwargs)
        self.dispatcher = cherrypy.dispatch.RoutesDispatcher()
        self.merge({'/': {'request.dispatch': self.dispatcher}})

        # Configure routes
        self.dispatcher.connect('root', '/', Root(), action='index')
        self._resource('package', 'packages', Packages())
        self._resource(
            'version', 'versions', PackageVersions(), parent_resource={
                'member_name': 'package',
                'collection_name': 'packages'
            })

    def _resource(self, member_name, collection_name, controller, **kwargs):
        """Configure routes for a resource.

        This generally has the same semantics as Mapper#resource, except for the
        mandatory controller argument, which takes a CherryPy handler instead of
        a string.
        """
        self.dispatcher.controllers[collection_name] = controller
        self.dispatcher.mapper.resource(member_name, collection_name, **kwargs)

if __name__ == "__main__":
    run_wsgi_app(Application())
