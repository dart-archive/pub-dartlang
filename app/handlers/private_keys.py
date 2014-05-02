# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import cherrypy

from google.appengine.api import users

import handlers
from models.private_key import PrivateKey

class PrivateKeys(object):
    """The handler for /private-keys/*.

    The private keys should only need to be set once, but it's still useful to
    have a nice interface for doing so. This is that interface.
    """

    @handlers.handle_validation_errors
    def create(self, oauth_key, api_key):
        """Set the private keys."""
        if not users.is_current_user_admin():
            handlers.http_error(403, "Only admins may set the private keys.")
        PrivateKey.set_oauth(oauth_key)
        PrivateKey.set_api(api_key)
        handlers.flash("Private keys set successfully.")
        raise cherrypy.HTTPRedirect("/admin#tab-private-keys")
