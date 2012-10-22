# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from google.appengine.api import oauth
from google.appengine.api import users

import handlers
import models

class PackageUploaders(object):
    """The handler for packages/*/uploaders/*.

    This handler is in charge of the list of users that are allowed to upload a
    given package.
    """

    @handlers.json_action
    @models.transactional
    def create(self, package_id, format, email):
        """Add a new uploader for this package.

        Only other uploaders may add new uploaders."""

        package = handlers.request().package
        if oauth.get_current_user() not in package.uploaders:
            handlers.json_error(
                403, "You aren't an uploader for package '%s'." %
                         package.name)

        package.uploaders.append(users.User(email))
        package.put()
        return handlers.json_success(
            "'%s' added as an uploader for package '%s'." %
                (email, package.name))
