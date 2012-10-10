# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import cherrypy

from google.appengine.api import users

import handlers
from models.private_key import PrivateKey

class PrivateKeys(object):
    """The handler for /private-keys/*.

    The private key should only need to be set once, but it's still useful to
    have a nice interface for doing so. This is that interface.
    """

    @handlers.handle_validation_errors
    def create(self, key):
        """Set the private key."""
        if not users.is_current_user_admin():
            handlers.http_error(403, "Only admins may set the private key.")
        PrivateKey.set(key)
        handlers.flash("Private key set successfully.")
        raise cherrypy.HTTPRedirect("/admin")
