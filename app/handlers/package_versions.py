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
    """The handler for packages/*/versions/*.

    This handler is in charge of individual versions of packages.
    """

    def index(self, package_id):
        """Retrieve a list of all versions for a given package."""
        package = handlers.request().package
        return handlers.render(
            "packages/versions/index", package=package,
            versions=package.version_set.order('-sort_order').run(),
            layout={'title': 'All versions of %s' % package.name})

    def show(self, package_id, id, format):
        """Retrieve the page describing a package version.

        Depending on the format, this could be a user-readable webpage (.html),
        a machine-readable YAML document (.yaml), or a download of the actual
        package blob (.tar.gz).
        """

        # The built-in format parsing has trouble with versions since they
        # contain periods, so we have to undo it and apply our own.
        id = '%s.%s' % (id, format)
        if id.endswith('.tar.gz'):
            id = id[0:-len('.tar.gz')]
            version = handlers.request().package_version(id)
            deferred.defer(self._count_download, version.key())
            raise cherrypy.HTTPRedirect(version.download_url)
        elif id.endswith('.yaml'):
            id = id[0:-len('.yaml')]
            version = handlers.request().package_version(id)
            cherrypy.response.headers['Content-Type'] = 'text/yaml'
            return version.pubspec.to_yaml()
        else:
            handlers.http_error(404)

    def _count_download(self, key):
        """Increment the download count for a package version."""
        with models.transaction():
            version = PackageVersion.get(key)
            version.downloads += 1
            version.package.downloads += 1
            version.put()
            version.package.put()

    @handlers.json_action
    @handlers.requires_private_key
    @handlers.requires_uploader
    def new_dartdoc(self, package_id, id, format):
        """Retrieve the form for uploading dartdoc for this package version."""
        if PrivateKey.get() is None:
            handlers.http_error(500, 'No private key set.')

        version = handlers.request().package_version(id)
        upload = cloud_storage.Upload(version.dartdoc_storage_path,
                                      acl='public-read',
                                      size_range=(0, Package.MAX_SIZE))

        return upload.to_json()

    def reload(self):
        """Reload all package versions from their tarballs."""
        if not handlers.is_current_user_dogfooder(): handlers.http_error(403)
        query = PackageVersion.all(keys_only=True)
        memcache.set('versions_to_reload', query.count())
        memcache.set('versions_reloaded', 0)

        for key in query.run():
            name = 'reload-%s-%s' % (int(time.time()), key)
            deferred.defer(self._reload_version, key, _name=name)
        raise cherrypy.HTTPRedirect('/admin#tab-packages')

    def _reload_version(self, key):
        """Reload a single package version from its tarball."""

        version = PackageVersion.get(key)
        logging.info('Reloading %s %s' % (version.package.name, version.version))

        with closing(cloud_storage.read(version.storage_path)) as f:
            new_version = PackageVersion.from_archive(
                f, uploader=version.uploader)

        with models.transaction():
            # Reload the old version in case anything (e.g. sort order) changed.
            version = PackageVersion.get(key)
            package = version.package

            # We don't load new_version.package.latest_version here for two
            # reasons. One is to avoid a needless data store lookup; the other
            # is because it's possible that that version is being reloaded in
            # another transaction and thus in a weird transitional state.
            latest_version_key = Package.latest_version.get_value_for_datastore(
                package)
            if latest_version_key == key:
                package.latest_version = new_version

            new_version.created = version.created
            new_version.downloads = version.downloads
            new_version.sort_order = version.sort_order
            version.delete()
            new_version.put()

            # Only save the package if its latest version has been updated.
            # Otherwise, its latest version may be being updated in parallel,
            # causing icky bugs.
            if latest_version_key == key:
                package.put()

        count = memcache.incr('versions_reloaded')
        logging.info('%s/%s versions reloaded' %
                     (count, memcache.get('versions_to_reload')))

    @handlers.json_action
    def reload_status(self, format):
        """Return the status of the current package reload.

        This is a JSON map. If the reload is finished, it will contain only a
        'done' key with value true. If the reload is in progress, it will
        contain 'count' and 'total' keys, indicating the total number of
        packages to reload and the number that have been reloaded so far,
        respectively.
        """
        if not users.is_current_user_admin():
            handlers.http_error(403, "Permission denied.")
        reload_status = PackageVersion.get_reload_status()
        return json.dumps(reload_status or {'done': True})
