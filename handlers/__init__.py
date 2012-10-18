# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

"""This module provides utility functions for handlers."""

import os

import cherrypy
from decorator import decorator
from google.appengine.api import oauth
from google.appengine.api import users
from google.appengine.ext import db
import json
import pystache
import routes

from models.package import Package
from models.package_version import PackageVersion

_renderer = pystache.Renderer(search_dirs = [
        os.path.join(os.path.dirname(__file__), '../views')])

def render(name, *context, **kwargs):
    """Renders a Mustache template with the standard layout.

    The interface of this function is the same as pystache.Renderer.render,
    except that it takes the name of a template instead of the template string
    itself. These templates are located in views/.

    This also surrounds the rendered template in the layout template (located in
    views/layout.mustache), unless layout=False is passed."""

    kwargs_for_layout = kwargs.pop('layout', {})
    content = _renderer.render(
        _renderer.load_template(name), *context, **kwargs)
    if kwargs_for_layout == False: return content
    return layout(content, **kwargs_for_layout)

def layout(content, title=None):
    """Renders a Mustache layout with the given content."""

    # We're about to display the flash message, so we should get rid of the
    # cookie containing it.
    cherrypy.response.cookie['flash'] = ''
    cherrypy.response.cookie['flash']['expires'] = 0
    cherrypy.response.cookie['flash']['path'] = '/'
    flash = cherrypy.request.cookie.get('flash')

    if title is not None:
        title += ' | '
    else:
        title = ''
    title = '%sPub Package Manager' % title

    return _renderer.render(
        _renderer.load_template("layout"),
        content=content,
        logged_in=users.get_current_user() is not None,
        login_url=users.create_login_url(cherrypy.url()),
        logout_url=users.create_logout_url(cherrypy.url()),
        message=flash and flash.value,
        title=title)

def flash(message):
    """Records a message for the user.

    This message will be displayed and cleared next time a page is rendered for
    the user. Redirects and error pages will not clear the message."""
    cherrypy.response.cookie['flash'] = message
    cherrypy.response.cookie['flash']['path'] = '/'

def http_error(status, message=None):
    """Throw an HTTP error.

    This raises a cherrypy.HTTPError after ensuring that the error message is a
    str object and not a unicode object.
    """
    if message: message = message.encode('utf-8')
    raise cherrypy.HTTPError(status, message)

def json_error(status, message):
    """Throw an HTTP error for a JSON response.

    This wraps the error message in a JSON object.
    """
    message = message.encode('utf-8')
    raise JsonError(status, message)

class JsonError(cherrypy.HTTPError):
    """The error class for JSON responses.

    This class causes a JSON-formatted response, with the correct content-type.
    """

    def set_response(self):
        """Set the response data for this error."""
        cherrypy.response.status = self.status
        cherrypy.response.headers['Content-Type'] = 'application/json'
        cherrypy.response.body = json.dumps({
            "error": {"message": self._message}
        })

@decorator
def handle_validation_errors(fn, *args, **kwargs):
    """Convert validation errors into user-friendly behavior.

    This is a decorator that catches validation errors for models, displays them
    in the flash text, and redirects the user back to the create or edit page
    for said models.
    """

    try: return fn(*args, **kwargs)
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

def get_current_user():
    """Return the current db.User object, or None.

    Unlike users.get_current_user, this will return the user object for OAuth
    requests as well.
    """
    user = users.get_current_user()
    if user: return user
    try: return oauth.get_current_user()
    except oauth.OAuthRequestError, e: return None

_OAUTH_ADMINS = [
    'gram@google.com',
    'jmesserly@google.com',
    'nweiz@google.com',
    'rnystrom@google.com',
    'sethladd@google.com',
    'sigmund@google.com',
    'vsm@google.com',
]
"""Emails of administrators for this app.

AppEngine keeps track of these automatically for normal browser requests, but it
doesn't store the admin bit in a way that's accessible from OAuth, so we have to
store a copy of these here.

From https://appengine.google.com/permissions?&app_id=s~dartlang-pub.
"""

def is_current_user_admin():
    """Return whether there is a logged-in admin.

    Unlike users.is_current_user_admin, this will return true if an admin is
    logged in via OAuth.
    """
    return users.is_current_user_admin() or \
        os.environ.get('OAUTH_IS_ADMIN') == '1'

def is_production():
    """Return whether we're running in production mode."""
    return bool(os.environ.get('DATACENTER'))

def is_dev_server():
    """Return whether we're running on locally or on AppEngine.

    Note that this returns True in tests so that the test appear to run in a
    non-dev-server-like environment.
    """
    return os.environ['SERVER_SOFTWARE'].startswith('Development')

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
        self._package_version = None

    def url(self, **kwargs):
        """Construct a URL for a given set of parametters.

        This takes the given parameters and merges them with the parameters for
        the current request to produce the resulting URL.
        """
        params = self.route.copy()
        params.update(kwargs)
        return self.request.base + routes.url_for(**params)

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
        package = self.maybe_package
        if package: return package
        name = self._package_name
        if name is None: http_error(403, "No package name found.")
        http_error(404, "Package \"%s\" doesn't exist." % name)

    @property
    def maybe_package(self):
        """Load the current package object.

        This auto-detects the package name from the request parameters. If the
        package doesn't exist, returns None.
        """

        if self._package: return self._package

        name = self._package_name
        if name is None: return None

        self._package = Package.get_by_key_name(name)
        if self._package: return self._package
        return None

    @property
    def _package_name(self):
        """Return the name of the current package."""
        if self.route['controller'] == 'packages':
            return self.request.params['id']
        else:
            return self.request.params['package_id']

    def package_version(self, version):
        """Load the current package version object.

        This auto-detects the package name from the request parameters. If the
        package version doesn't exist, throws a 404 error.
        """

        if self._package_version: return self._package_version

        package_name = self.request.params['package_id']
        if not package_name:
            http_error(403, "No package name found.")

        self._package_version = PackageVersion.get_by_name_and_version(
            package_name, version)
        if self._package_version: return self._package_version
        http_error(404, "\"%s\" version %s doesn't exist." %
                   (package_name, version))
