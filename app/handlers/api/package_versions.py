# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from cStringIO import StringIO
from contextlib import closing
from uuid import uuid4
import json
import logging
import time

import cherrypy
import routes
from google.appengine.ext import db
from google.appengine.ext import deferred
from google.appengine.api import files
from google.appengine.api import memcache
from google.appengine.api import oauth
from google.appengine.api import users

import handlers
import models
from handlers import cloud_storage
from models.package import Package
from models.package_version import PackageVersion
from models.private_key import PrivateKey

class PackageVersions(object):
    """The handler for /api/packages/*/versions/*."""

    @handlers.api(1)
    @handlers.requires_private_key
    @handlers.requires_uploader
    def new(self, format=''):
        """Retrieve the form for uploading a package version.

        This accepts arbitrary keyword arguments to support OAuth.
        """
        id = str(uuid4())
        redirect_url = handlers.request().url(action="create", id=id)
        upload = cloud_storage.Upload("tmp/" + id, acl="project-private",
                                      size_range=(0, Package.MAX_SIZE),
                                      success_redirect=redirect_url)

        # If the package hasn't been validated and moved out of tmp in five
        # minutes, delete it. This could happen if the user uploads the package
        # to cloud storage, but closes the browser before "create" is run.
        deferred.defer(self._remove_tmp_package, id, _countdown=5*60)

        return upload.to_json()

    def _remove_tmp_package(self, id):
        """Try to remove an orphaned package upload."""
        try: cloud_storage.delete_object("tmp/" + id)
        except: logging.error('Error deleting temporary object ' + id)

    @handlers.api(1)
    @handlers.handle_validation_errors
    @handlers.requires_uploader
    def create(self, id, **kwargs):
        """Create a new package version.

        This creates a single package version. It will also create all the
        package metadata if that doesn't already exist. The package archive is
        uploaded to cloud storage separately.

        If the user doesn't own the package or isn't logged in with admin
        privileges, this will return a 403. If the package already has a version
        with this number, or if the version is invalid, this will return a 400.

        Arguments:
          id: The id of the package in cloud storage.
        """

        try:
            route = handlers.request().route
            if 'id' in route: del route['id']

            try:
                with closing(cloud_storage.read('tmp/' + id)) as f:
                    version = PackageVersion.from_archive(
                        f, uploader=handlers.get_oauth_user())
            except (KeyError, files.ExistenceError):
                handlers.http_error(
                    403, "Package upload " + id + " does not exist.")

            # If the package for this version already exists, make sure we're an
            # uploader for it. If it doesn't, we're fine to create it anew.
            if version.package.is_saved():
                if not version.package.has_uploader(handlers.get_oauth_user()):
                    handlers.http_error(
                        403, "You aren't an uploader for package '%s'." %
                                 version.package.name)
                elif version.package.has_version(version.version):
                    message = 'Package "%s" already has version "%s".' % \
                        (version.package.name, version.version)
                    handlers.http_error(400, message)

                if self._should_update_latest_version(version):
                    version.package.latest_version = version
            else:
                version.package.latest_version = version

            cloud_storage.modify_object(version.storage_path,
                                        acl='public-read',
                                        copy_source='tmp/' + id)

            with models.transaction():
                version.package.put()
                version.put()

            deferred.defer(self._compute_version_order, version.package.name)

            return handlers.json_success('%s %s uploaded successfully.' %
                (version.package.name, version.version))
        finally:
            cloud_storage.delete_object('tmp/' + id)

    def _compute_version_order(self, name):
        """Compute the sort order for all versions of a given package."""
        versions = list(Package.get_by_key_name(name).version_set.run())
        versions.sort(key=lambda version: version.version)
        for i, version in enumerate(versions):
            version.sort_order = i
        with models.transaction():
            for version in versions: version.put()

    def _should_update_latest_version(self, new):
        """Whether or not the latest version of a package should be updated.

        'new' is the newly uploaded version of the package to check.
        """
        old = new.package.latest_version
        if old is None: return True
        was_prerelease = old.version.is_prerelease
        is_prerelease = new.version.is_prerelease
        if was_prerelease != is_prerelease: return was_prerelease
        return old.version < new.version

    @handlers.api(1)
    @handlers.requires_private_key
    def upload(self, file, key, acl=None, policy=None, signature=None,
               success_action_redirect=None, **kwargs):
        """A development-only action for uploading a package archive.

        In production, package archives are uploaded directly to cloud storage,
        using a signed form for authentication. The signed form doesn't work for
        the development server, since it uses a local database in place of cloud
        storage, so this action emulates it by manually saving the file to the
        development database.
        """

        if handlers.is_production(): raise handlers.http_error(404)
        if PrivateKey.sign(policy) != signature: raise handlers.http_error(403)

        write_path = files.gs.create('/gs/' + key, acl=acl)
        with files.open(write_path, 'a') as f:
            f.write(file.file.read())
        files.finalize(write_path)

        if success_action_redirect:
            raise cherrypy.HTTPRedirect(success_action_redirect)
        cherrypy.response.status = 204
        return ""

    @handlers.api(2)
    def show(self, package_id, id, format=None):
        """Retrieve the document describing a package version."""
        # The mapper expects anything past a period to be the format of the
        # document, which is fine for "index.html" or "packages.json" but not
        # for "1.2.3". It thinks "3" is the format, which is wrong, so we add it
        # on here.
        if format: id = id + '.' + format
        return json.dumps(
            handlers.request().package_version(id).as_dict(full=True))

    @handlers.api(1)
    @handlers.requires_private_key
    @handlers.requires_uploader
    def new_dartdoc(self, package_id, id):
        """Retrieve the form for uploading dartdoc for this package version."""
        version = handlers.request().package_version(id)
        upload = cloud_storage.Upload(version.dartdoc_storage_path,
                                      acl='public-read',
                                      size_range=(0, Package.MAX_SIZE))

        return upload.to_json()
