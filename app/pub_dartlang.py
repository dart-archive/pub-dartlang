# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

"""The entrypoint for the pub.dartlang.org server.

In development, this should be run using the App Engine dev_appserver.py script.
"""

import json
import logging

import cherrypy
from google.appengine.api import users
from google.appengine.ext.webapp.util import run_wsgi_app

import handlers
import handlers.api as api
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

        # Frontend routes (also deprecated v1 API routes)
        self.dispatcher.connect('root', '/', Root(), action='index')
        self.dispatcher.mapper.connect(
            '/authorized', controller='root', action='authorized')
        self.dispatcher.mapper.connect(
            '/site-map', controller='root', action='site_map')
        self.dispatcher.mapper.connect(
            '/search', controller='root', action='search')
        self.dispatcher.mapper.connect(
            '/admin', controller='root', action='admin')
        self.dispatcher.mapper.connect(
            '/gs_/{filename:.*?}', controller='root', action='serve')

        self.dispatcher.connect('doc', '/doc', Doc(), action='index')
        self.dispatcher.connect('doc', '/doc/{path:.*?}', Doc(), action='show')

        self._resource('package', 'packages', Packages())
        self._resource('private-key', 'private-keys', PrivateKeys())

        self._resource('version', 'versions', PackageVersions(),
                       parent_resource={
                         'member_name': 'package',
                         'collection_name': 'packages'
                       },
                       member={
                         'create': 'GET',
                         'new_dartdoc': 'GET'
                       })
        with self.dispatcher.mapper.submapper(
                controller='versions',
                path_prefix='/packages/versions/') as m:
            m.connect('reload', action='reload', conditions={'method': 'POST'})
            m.connect('reload.:(format)', action='reload_status',
                      conditions={'method': 'GET'})

        self._resource('uploader', 'uploaders', PackageUploaders(),
                       parent_resource={
                         'member_name': 'package',
                         'collection_name': 'packages'
                       })

        # API Routes
        self.dispatcher.connect('api.root', '/api', api.Root(), action='index')

        self.dispatcher.controllers['api.packages'] = api.Packages()
        self.dispatcher.mapper.resource(
            'package', 'packages',
            controller='api.packages', path_prefix='api')

        self.dispatcher.controllers['api.versions'] = api.PackageVersions()
        self.dispatcher.mapper.resource(
            'version', 'versions',
            controller='api.versions',
            path_prefix='api/packages/:package_id',
            parent_resource={
                'member_name': 'package',
                'collection_name': 'packages'
            },
            member={
                'create': 'GET',
                'new_dartdoc': 'GET'
            })

        with self.dispatcher.mapper.submapper(
                controller='api.versions',
                path_prefix='/api/packages/versions/') as m:
            m.connect('new', action='new',
                      conditions={'method': ['GET', 'HEAD']})
            m.connect(':id/create', action='create')
            m.connect('upload', action='upload', conditions={'method': 'POST'})

        self.dispatcher.controllers['api.uploaders'] = api.PackageUploaders()
        self.dispatcher.mapper.resource(
            'uploader', 'uploaders',
            controller='api.uploaders',
            path_prefix='api/packages/:package_id',
            parent_resource={
                'member_name': 'package',
                'collection_name': 'packages'
            })

        # For old API endpoints that are compatible with the new API, we can
        # just reroute the old paths to the new actions.
        with self.dispatcher.mapper.submapper(
                controller='api.versions',
                path_prefix='/packages/versions/') as m:
            m.connect('new.:(format)', action='new',
                      conditions={'method': ['GET', 'HEAD']})
            m.connect('new', action='new',
                      conditions={'method': ['GET', 'HEAD']})
            m.connect(':id/create', action='create')
            m.connect(':id/create.:(format)', action='create')
            m.connect('upload', action='upload', conditions={'method': 'POST'})

        # Set up custom error page.
        cherrypy.config.update({'error_page.default': _error_page})

        # This logging is redundant with AppEngine's built-in logging, and
        # sometimes prints error logs where there should only be info logs.
        self.log.access_log.setLevel(logging.WARNING)

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
        handlers.JsonError(status, message).set_response()
        return cherrypy.response.body

    return str(handlers.render('error',
        status=status,
        message=message,
        traceback=traceback,
        layout={'title': 'Error %s' % status}))

app = Application()

if __name__ == "__main__":
    run_wsgi_app(app)
