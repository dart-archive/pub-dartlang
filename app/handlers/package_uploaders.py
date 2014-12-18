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
    @handlers.requires_uploader
    @models.transactional
    def create(self, package_id, format, email):
        """Add a new uploader for this package.

        Only other uploaders may add new uploaders."""

        package = handlers.request().package
        user_to_add = users.User(email)
        if package.has_uploader(user_to_add):
            handlers.http_error(
                400, "User '%s' is already an uploader for package '%s'." %
                         (email, package.name))

        package.uploaders.append(user_to_add)
        package.temp_synchronize_uploaders_to_uploaderemails()
        package.put()
        package.invalidate_cache()
        return handlers.json_success(
            "'%s' added as an uploader for package '%s'." %
                (email, package.name))

    @handlers.json_action
    @handlers.requires_uploader
    @models.transactional
    def delete(self, package_id, id, format):
        """Delete one of this package's uploaders.

        Only uploaders may delete uploaders. If only one uploader remains, that
        uploader may not be deleted until a new one is added.
        """

        package = handlers.request().package
        user_to_delete = users.User(id)
        if not package.has_uploader(user_to_delete):
            handlers.http_error(
                400, "'%s' isn't an uploader for package '%s'." %
                         (user_to_delete.nickname(), package.name))

        if len(package.uploaders) == 1:
            handlers.http_error(
                400, ("Package '%s' only has one uploader, so that uploader " +
                          "can't be removed.") % package.name)

        email_to_delete = user_to_delete.email().lower()
        package.uploaders = [uploader for uploader in package.uploaders
                             if uploader.email().lower() != email_to_delete]
        package.temp_synchronize_uploaders_to_uploaderemails()
        package.put()
        package.invalidate_cache()
        return handlers.json_success(
            "'%s' is no longer an uploader for package '%s'." %
                (id, package.name))
