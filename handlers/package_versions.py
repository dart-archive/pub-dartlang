# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from cStringIO import StringIO
from contextlib import closing
from uuid import uuid4
import json
import logging

import cherrypy
import routes
from google.appengine.ext import db
from google.appengine.ext import deferred
from google.appengine.api import files
from google.appengine.api import memcache
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

    def new(self, package_id):
        """Retrieve the form for uploading a package version.

        If the user isn't logged in, this presents a login screen. If they are
        logged in but don't have admin priviliges or don't own the package, this
        redirects to /packages/.
        """
        user = users.get_current_user()
        package = handlers.request().maybe_package
        if not user:
            raise cherrypy.HTTPRedirect(
                users.create_login_url(cherrypy.url()))
        elif package and package.owner != user:
            handlers.flash("You don't down package '%s'" % package.name)
            raise cherrypy.HTTPRedirect('/packages/%s' % package.name)
        elif not users.is_current_user_admin():
            handlers.flash('Currently only admins may create packages.')
            raise cherrypy.HTTPRedirect('/packages')
        elif PrivateKey.get() is None:
            raise cherrypy.HTTPRedirect('/admin#tab-private-key')

        id = str(uuid4())
        redirect_url = handlers.request().url(action="create", id=id)
        form = cloud_storage.upload_form("tmp/" + id, acl="project-private",
                                         size_range=(0, Package.MAX_SIZE),
                                         success_redirect=redirect_url)

        # If the package hasn't been validated and moved out of tmp in five
        # minutes, delete it. This could happen if the user uploads the package
        # to cloud storage, but closes the browser before "create" is run.
        deferred.defer(self._remove_tmp_package, id, _countdown=5*60)

        if package is not None:
            title = 'Upload a new version of %s' % package.name
        else:
            title = 'Upload a new package'

        return handlers.render("packages/versions/new",
                               form=form, package=package,
                               layout={'title': title})

    def _remove_tmp_package(self, id):
        """Try to remove an orphaned package upload."""
        try: cloud_storage.delete_object("tmp/" + id)
        except: logging.error('Error deleting temporary object ' + id)

    @handlers.handle_validation_errors
    def create(self, package_id, id):
        """Create a new package version.

        This creates a single package version. It will also create all the
        package metadata if that doesn't already exist. The package archive is
        uploaded to cloud storage separately.

        If the user doesn't own the package or isn't logged in with admin
        privileges, this will return a 403. If the package already has a version
        with this number, or if the version is invalid, this will redirect to
        the new version form.

        Arguments:
          id: The id of the package in cloud storage.
        """

        try:
            route = handlers.request().route
            if 'id' in route: del route['id']

            package = handlers.request().maybe_package
            if package and package.owner != users.get_current_user():
                handlers.http_error(
                    403, "You don't down package '%s'" % package.name)
            elif not users.is_current_user_admin():
                handlers.http_error(403, "Only admins may create packages.")

            try:
                with closing(cloud_storage.read('tmp/' + id)) as f:
                    version = PackageVersion.from_archive(f)
            except (KeyError, files.ExistenceError):
                handlers.http_error(
                    403, "Package upload " + id + " does not exist.")

            if version.package.is_saved():
                if version.package.owner != users.get_current_user():
                    handlers.http_error(
                        403, "You don't own package '%s'." % package.name)
                elif version.package.has_version(version.version):
                    handlers.flash('Package "%s" already has version "%s".' %
                                   (version.package.name, version.version))
                    url = handlers.request().url(
                        action='new', package_id=version.package.name)
                    raise cherrypy.HTTPRedirect(url)

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

            handlers.flash('%s %s uploaded successfully.' %
                           (version.package.name, version.version))
            raise cherrypy.HTTPRedirect('/packages/%s' % version.package.name)
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
        if was_prerelease and not is_prerelease: return True
        if is_prerelease and not was_prerelease: return False
        return old.version < new.version

    def upload(self, package_id, file, key, acl=None, policy=None,
               signature=None, success_action_redirect=None, **kwargs):
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

    def reload(self, package_id):
        """Reload all package versions from their tarballs."""
        if not users.is_current_user_admin(): handlers.http_error(403)
        versions_to_reload = 0
        for key in PackageVersion.all(keys_only=True).run():
            versions_to_reload += 1
            deferred.defer(self._reload_version, key)
        memcache.set('versions_to_reload', versions_to_reload)
        memcache.set('versions_reloaded', 0)
        raise cherrypy.HTTPRedirect('/admin#tab-packages')

    def _reload_version(self, key):
        """Reload a single package version from its tarball."""

        version = PackageVersion.get(key)
        with closing(cloud_storage.read(version.storage_path)) as f:
            new_version = PackageVersion.from_archive(f)

        with models.transaction():
            # Reload the old version in case anything (e.g. sort order) changed.
            version = PackageVersion.get(key)
            if new_version.package.latest_version == version:
                new_version.package.latest_version = new_version
            new_version.created = version.created
            new_version.downloads = version.downloads
            new_version.sort_order = version.sort_order
            version.delete()
            new_version.put()
            new_version.package.put()

        memcache.incr('versions_reloaded')

    def reload_status(self, package_id):
        """Return the status of the current package reload.

        This is a JSON map. If the reload is finished, it will contain only a
        'done' key with value true. If the reload is in progress, it will
        contain 'count' and 'total' keys, indicating the total number of
        packages to reload and the number that have been reloaded so far,
        respectively.
        """
        if not users.is_current_user_admin(): cherrypy.http_error(403)
        cherrypy.response.headers['Content-Type'] = 'application/json'
        reload_status = PackageVersion.get_reload_status()
        return json.dumps(reload_status or {'done': True})
