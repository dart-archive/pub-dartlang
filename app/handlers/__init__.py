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
from models.private_key import PrivateKey

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

    package = request().maybe_package

    return _renderer.render(
        _renderer.load_template("layout"),
        content=content,
        logged_in=users.get_current_user() is not None,
        login_url=users.create_login_url(cherrypy.url()),
        logout_url=users.create_logout_url(cherrypy.url()),
        message=flash and flash.value,
        title=title,
        package=package)

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

class JsonError(cherrypy.HTTPError):
    """The error class for JSON responses.

    This class causes a JSON-formatted response, with the correct content-type.
    It's usually unneccessary to throw this directly, since json_action takes
    care of converting other exceptions.
    """

    def set_response(self):
        """Set the response data for this error."""
        authenticate = 'Bearer'
        if request().has_oauth and self.status in [400, 401, 403]:
            authenticate += ' error="%s"' % {
                400: 'invalid_request',
                401: 'invalid_token',
                403: 'insufficient_scope'
            }[self.status]
            authenticate += ', scope="%s"' % OAUTH2_SCOPE
            if self.message:
                authenticate += ', error_description="%s"' % self.message
        cherrypy.response.headers['WWW-Authenticate'] = authenticate

        cherrypy.response.status = self.status
        cherrypy.response.headers['Content-Type'] = 'application/json'
        cherrypy.response.body = json.dumps({
            "error": {"message": self._message}
        })

def json_success(message):
    """Return a successful JSON response."""
    cherrypy.response.headers['Content-Type'] = 'application/json'
    return json.dumps({"success": {"message": message}})

@decorator
def handle_validation_errors(fn, *args, **kwargs):
    """Convert validation errors into user-friendly behavior.

    This is a decorator that catches validation errors for models, displays them
    in the flash text, and redirects the user back to the create or edit page
    for said models.
    """

    try: return fn(*args, **kwargs)
    except (db.BadKeyError, db.BadValueError) as err:
        if request().is_json: json_error(400, str(err))

        flash(err)

        new_action = 'index'
        if request().route['action'] == 'create':
            new_action = 'new'
        elif request().route['action'] == 'update':
            new_action = 'edit'

        # TODO(nweiz): auto-fill the form values from
        # cherrypy.request.params
        raise cherrypy.HTTPRedirect(request().url(action=new_action))

@decorator
def json_or_html_action(fn, *args, **kwargs):
    """A decorator for actions that can be JSON-formatted.

    If the current request is JSON-formatted, this sets the content-type and
    ensures that any errors are JSON-formatted. Otherwise, the request proceeds
    unaltered.
    """

    if not request().is_json: return fn(*args, **kwargs)

    try:
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return fn(*args, **kwargs)
    except JsonError as err:
        raise err
    except cherrypy.HTTPError as err:
        raise JsonError(err.status, err._message)
    except (db.BadKeyError, db.BadValueError) as err:
        raise JsonError(400, err.message)
    except oauth.OAuthRequestError as err:
        raise JsonError(403, "OAuth2 authentication failed.")

@decorator
@json_or_html_action
def json_action(fn, *args, **kwargs):
    """A decorator for actions that support only JSON.

    This implies json_or_html_action.
    """
    if not request().is_json: http_error(404)
    return fn(*args, **kwargs)

@decorator
def requires_user(fn, *args, **kwargs):
    """A decorator for actions that require a logged-in user.

    For JSON actions, this checks for an OAuth2 user. If none is found, this
    raises an appropriately-formatted 401 error.

    For HTML actions, this checks for a user logged in via cookies. If none is
    found, this redirects to the login page.
    """

    user = get_current_user()
    if user: return fn(*args, **kwargs)

    if request().is_json:
        http_error(401, 'OAuth2 authentication failed.')
    else:
        raise cherrypy.HTTPRedirect(users.create_login_url(cherrypy.url()))

@decorator
@requires_user
def requires_uploader(fn, *args, **kwargs):
    """A decorator for actions that require an uploader of the current package.

    This implies requires_user. It does not require that a package exist; if
    none does, it only checks that the user has permission to upload packages at
    all.

    Admins have uploader rights for all packages.
    """

    if is_current_user_admin(): return fn(*args, **kwargs)

    package = request().maybe_package
    if package and not package.has_uploader(get_current_user()):
        message = "You aren't an uploader for package '%s'." % package.name
        if request().is_json:
            http_error(403, message)
        else:
            flash(message)
            raise cherrypy.HTTPRedirect('/packages/%s' % package.name)

    return fn(*args, **kwargs)

@decorator
def requires_private_key(fn, *args, **kwargs):
    """A decorator for actions that require a private key to be set."""
    if PrivateKey.get() is None: http_error(500, 'No private key set.')
    return fn(*args, **kwargs)

def get_current_user():
    """Return the current db.User object, or None.

    Unlike users.get_current_user, this will return the user object for OAuth
    requests as well.
    """
    user = users.get_current_user()
    if user: return user
    try:
        return get_oauth_user()
    except oauth.OAuthRequestError, e:
        return None

OAUTH2_SCOPE = 'https://www.googleapis.com/auth/userinfo.email'
"""The scope needed for OAuth2 requests."""

def get_oauth_user():
    """Return the OAuth db.User object.

    Throws an oauth.OAuthRequestError if the OAuth request is invalid.
    """
    return oauth.get_current_user(OAUTH2_SCOPE)

def is_current_user_admin():
    """Return whether there is a logged-in admin.

    Unlike users.is_current_user_admin, this will return true if an admin is
    logged in via OAuth.
    """
    if users.is_current_user_admin(): return True

    # The OAUTH_IS_ADMIN variable is only set once oauth.get_current_user is
    # called.
    get_current_user()
    return os.environ.get('OAUTH_IS_ADMIN') == '1'

def is_current_user_dogfooder():
    """Return whether the logged-in user has dogfood permissions.

    Dogfooders have more permissions than unknown users, but fewer than full-on
    admins. They exist to test features before they're ready to be rolled out to
    everyone.
    """

    # Admins have all permissions dogfooders do.
    if is_current_user_admin(): return True

    # Currently only Googlers are dogfooders.
    user = get_current_user()
    return user and user.email().endswith('@google.com')

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
    def is_json(self):
        """Whether the current request is JSON-formatted."""
        return self.request.params.get('format') == 'json'

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

    @property
    def has_oauth(self):
        """Return whether the request contains OAuth2 credentials.

        This doesn't check whether the credentials are valid, just that
        something that looks like credentials was sent.
        """
        try:
            get_oauth_user()
            return True
        except oauth.InvalidOAuthParametersError, e:
            # This is the exception raised when no OAuth2 credentials are found
            # at all.
            return False
        except oauth.OAuthRequestError, e:
            return True

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
