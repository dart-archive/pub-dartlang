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
            handlers.http_error(
                403, "You aren't an uploader for package '%s'." %
                         package.name)

        user_to_add = users.User(email)
        if user_to_add in package.uploaders:
            handlers.http_error(
                400, "User '%s' is already an uploader for package '%s'." %
                         (email, package.name))

        package.uploaders.append(user_to_add)
        package.put()
        return handlers.json_success(
            "'%s' added as an uploader for package '%s'." %
                (email, package.name))

    @handlers.json_action
    @models.transactional
    def delete(self, package_id, id, format):
        """Delete one of this package's uploaders.

        Only uploaders may delete uploaders. If only one uploader remains, that
        uploader may not be deleted until a new one is added.
        """

        package = handlers.request().package
        if oauth.get_current_user() not in package.uploaders:
            handlers.http_error(
                403, "You aren't an uploader for package '%s'." %
                         package.name)

        user_to_delete = users.User(id)
        if user_to_delete not in package.uploaders:
            handlers.http_error(
                400, "'%s' isn't an uploader for package '%s'." %
                         (user_to_delete.nickname(), package.name))

        if len(package.uploaders) == 1:
            handlers.http_error(
                400, ("Package '%s' only has one uploader, so that uploader " +
                          "can't be removed.") % package.name)

        package.uploaders.remove(user_to_delete)
        package.put()
        return handlers.json_success(
            "'%s' is no longer an uploader for package '%s'." %
                (id, package.name))
