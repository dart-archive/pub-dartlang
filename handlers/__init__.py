# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import os

import cherrypy
from google.appengine.api import users

import pystache

_renderer = pystache.Renderer(search_dirs = [
        os.path.join(os.path.dirname(__file__), '../views')])

def render(name, *context, **kwargs):
    content = _renderer.render(
        _renderer.load_template(name), *context, **kwargs)

    # We're about to display the flash message, so we should get rid of the
    # cookie containing it.
    cherrypy.response.cookie['flash'] = ''
    cherrypy.response.cookie['flash']['expires'] = 0
    cherrypy.response.cookie['flash']['path'] = '/'
    flash = cherrypy.request.cookie.get('flash')

    return _renderer.render(
        _renderer.load_template("layout"),
        content = content,
        logged_in = users.get_current_user() is not None,
        login_url = users.create_login_url(cherrypy.url()),
        logout_url = users.create_logout_url(cherrypy.url()),
        message = flash and flash.value)

def flash(message):
    cherrypy.response.cookie['flash'] = message
    cherrypy.response.cookie['flash']['path'] = '/'

def dispatch_by_method(**kwargs):
    @cherrypy.expose
    def dispatcher(self, *dispatcher_args, **dispatcher_kwargs):
        http_method = cherrypy.request.method
        if not http_method in kwargs:
            raise cherrypy.HTTPError(404, "The path '%s' was not found." %
                                            cherrypy.request.path_info)

        dispatchee = kwargs[http_method]
        cherrypy._cpdispatch.test_callable_spec(
            dispatchee, dispatcher_args, dispatcher_kwargs)
        dispatchee(self, *dispatcher_args, **dispatcher_kwargs)

    return dispatcher
