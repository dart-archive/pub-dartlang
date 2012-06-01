# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

"""This module provides utility functions for handlers."""

import os

import cherrypy
from decorator import decorator
from google.appengine.api import users
from google.appengine.ext import db
import pystache
import routes

from models.package import Package

_renderer = pystache.Renderer(search_dirs = [
        os.path.join(os.path.dirname(__file__), '../views')])

def render(name, *context, **kwargs):
    """Renders a Moustache template with the standard layout.

    The interface of this function is the same as pystache.Renderer.render,
    except that it takes the name of a template instead of the template string
    itself. These templates are located in views/.

    This also surrounds the rendered template in the layout template (located in
    views/layout.mustache)."""

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
    """Records a message for the user.

    This message will be displayed and cleared next time a page is rendered for
    the user. Redirects and error pages will not clear the message."""
    cherrypy.response.cookie['flash'] = message
    cherrypy.response.cookie['flash']['path'] = '/'

def http_error(status, message):
    """Throw an HTTP error.

    This raises a cherrypy.HTTPError after ensuring that the error message is a
    str object and not a unicode object.
    """
    raise cherrypy.HTTPError(status, message.encode('utf-8'))

@decorator
def handle_validation_errors(fn, *args, **kwargs):
    """Convert validation errors into user-friendly behavior.

    This is a decorator that catches validation errors for models, displays them
    in the flash text, and redirects the user back to the create or edit page
    for said models.
    """

    try: fn(*args, **kwargs)
    except (db.BadKeyError, db.BadValueError) as err:
        flash(err)

        new_action = 'index'
        if request().route['action'] == 'create':
            new_action = 'new'
        elif request().route['action'] == 'update':
            new_action = 'edit'

        # TODO(nweiz): auto-fill the form values from
        # cherrypy.request.params
        raise cherrypy.HTTPRedirect(request().url(action=new_action))

def request():
    """Return the current Request instance."""
    if not hasattr(cherrypy.request, 'pub_data'):
        setattr(cherrypy.request, 'pub_data', Request(cherrypy.request))
    return cherrypy.request.pub_data

class Request(object):
    """A collection of request-specific helpers."""

    def __init__(self, request):
        self.request = request
        self._route = None
        self._package = None

    def url(self, **kwargs):
        """Construct a URL for a given set of parametters.

        This takes the given parameters and merges them with the parameters for
        the current request to produce the resulting URL.
        """
        params = self.route.copy()
        params.update(kwargs)
        return routes.url_for(**params)

    @property
    def route(self):
        """Return the parsed route for the current request.

        Most route information is available in the request parameters, but the
        controller and action components get stripped out early.
        """
        if not self._route:
            mapper = routes.request_config().mapper
            self._route = mapper.match(self.request.path_info)
        return self._route

    @property
    def package(self):
        """Load the current package object.

        This auto-detects the package name from the request parameters. If the
        package doesn't exist, throws a 404 error.
        """

        if self._package: return self._package

        if self.route['controller'] == 'packages':
            package_name = self.request.params['id']
        else:
            package_name = self.request.params['package_id']
        if not package_name:
            http_error(403, "No package name found.")

        self._package = Package.get_by_key_name(package_name)
        if self._package: return self._package
        http_error(404, "Package \"%s\" doesn't exist." % package_name)
