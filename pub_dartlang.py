# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

"""The entrypoint for the pub.dartlang.org server.

In development, this should be run using the App Engine dev_appserver.py script.
"""

import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'third_party'))

import cherrypy
from google.appengine.api import users
from google.appengine.ext.webapp.util import run_wsgi_app

import handlers
from handlers.doc import Doc
from handlers.root import Root
from handlers.packages import Packages
from handlers.package_uploaders import PackageUploaders
from handlers.package_versions import PackageVersions
from handlers.private_keys import PrivateKeys

class Application(cherrypy.Application):
    """The pub.dartlang.org WSGI application."""

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(None, *args, **kwargs)
        self.dispatcher = cherrypy.dispatch.RoutesDispatcher()
        self.merge({'/': {'request.dispatch': self.dispatcher}})

        # Configure routes
        self.dispatcher.connect('root', '/', Root(), action='index')
        self.dispatcher.mapper.connect(
            '/authorized', controller='root', action='authorized')
        self.dispatcher.mapper.connect(
            '/site-map', controller='root', action='site_map')
        self.dispatcher.mapper.connect(
            '/admin', controller='root', action='admin')
        self.dispatcher.mapper.connect(
            '/gs_/{filename:.*?}', controller='root', action='serve')

        self.dispatcher.connect('doc', '/doc', Doc(), action='index')
        self.dispatcher.connect(
            'doc', '/doc/{filename:.*?}', Doc(), action='show')

        self._resource('package', 'packages', Packages())
        self._resource('private-key', 'private-keys', PrivateKeys())

        self._resource('version', 'versions', PackageVersions(),
                       parent_resource={
                         'member_name': 'package',
                         'collection_name': 'packages'
                       },
                       collection={'upload': 'POST'},
                       member={'create': 'GET'})

        # Package version actions related to uploading a new package need to
        # work without that package in the URL.
        with self.dispatcher.mapper.submapper(controller='versions',
                                              path_prefix='/packages/versions/',
                                              package_id=None) as m:
            m.connect('new.:(format)', action='new',
                      conditions={'method': ['GET', 'HEAD']})
            m.connect('new', action='new',
                      conditions={'method': ['GET', 'HEAD']})
            m.connect(':id/create', action='create')
            m.connect(':id/create.:(format)', action='create')
            m.connect('upload', action='upload', conditions={'method': 'POST'})
            m.connect('reload', action='reload', conditions={'method': 'POST'})
            m.connect('reload.:(format)', action='reload_status',
                      conditions={'method': 'GET'})
        self.dispatcher.mapper.connect('/packages/versions/create',
                                       controller='versions',
                                       action='create')

        self._resource('uploader', 'uploaders', PackageUploaders(),
                       parent_resource={
                         'member_name': 'package',
                         'collection_name': 'packages'
                       })

        # Set up custom error page.
        cherrypy.config.update({'error_page.default': _error_page})

    def _resource(self, member_name, collection_name, controller, **kwargs):
        """Configure routes for a resource.

        This generally has the same semantics as Mapper#resource, except for the
        mandatory controller argument, which takes a CherryPy handler instead of
        a string.
        """
        self.dispatcher.controllers[collection_name] = controller
        self.dispatcher.mapper.resource(member_name, collection_name, **kwargs)

def _error_page(status, message, traceback, version):
    # Don't show tracebacks to end users.
    if not handlers.is_dev_server() and not users.is_current_user_admin():
        traceback = None

    if handlers.request().is_json:
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps({'error': {'message': message}})

    return str(handlers.render('error',
        status=status,
        message=message,
        traceback=traceback,
        layout={'title': 'Error %s' % status}))

app = Application()

if __name__ == "__main__":
    run_wsgi_app(app)
