# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import copy
import json
import tarfile

from google.appengine.api import memcache
from google.appengine.ext import db
import yaml

import models
from semantic_version import SemanticVersion
from handlers import cloud_storage
from package import Package
from properties import PubspecProperty, ReadmeProperty, VersionProperty
from pubspec import Pubspec
from readme import Readme

class PackageVersion(db.Model):
    """The model for a single version of a package.

    This model contains the actual (compressed) blob of code for this version of
    the package.
    """

    version = VersionProperty(required=True)
    """The version of the package."""

    pubspec = PubspecProperty(required=True, indexed=False)
    """The package version's pubspec file."""
    
    readme = ReadmeProperty()
    """The README file."""

    changelog = ReadmeProperty()
    """The CHANGELOG file."""

    libraries = db.ListProperty(str)
    """All libraries that can be imported from this package version."""

    package = db.ReferenceProperty(Package,
                                   required=True,
                                   collection_name = "version_set")
    """The Package model for this package version."""

    # The following properties are not parsed from the package archive. They
    # need to be manually copied over to new PackageVersions in
    # handlers.PackageVersions._reload_version.

    created = db.DateTimeProperty(auto_now_add=True)
    """When this package version was created."""

    downloads = db.IntegerProperty(required=True, default=0)
    """The number of times this package version has been downloaded."""

    sort_order = db.IntegerProperty(default=-1)
    """The sort order for this version.

    Lower numbers indicate earlier versions."""

    uploader = db.UserProperty(required=True)
    """The user who uploaded this package version."""

    @classmethod
    def new(cls, **kwargs):
        """Construct a new package version.

        Unlike __init__, this infers some properties from others. In particular:

        - The version is inferred from the pubspec.
        - The key name is set to the version.
        - The parent entity is set to the package.
        """

        if 'pubspec' in kwargs and 'version' not in kwargs:
            kwargs['version'] = kwargs['pubspec'].required('version')

        if 'version' in kwargs and \
                not isinstance(kwargs['version'], SemanticVersion):
            kwargs['version'] = SemanticVersion(kwargs['version'])

        if not 'key_name' in kwargs and not 'key' in kwargs:
            kwargs['key_name'] = str(kwargs['version'].canonical)

        if not 'parent' in kwargs:
            kwargs['parent'] = kwargs['package']

        version = cls(**kwargs)
        version._validate_fields_match_pubspec()
        return version

    @classmethod
    def from_archive(cls, file, uploader):
        """Load a package version from a .tar.gz archive.

        If the package specified in the archive already exists, it will be
        loaded and assigned as the package version's package. If it doesn't, a
        new package will be created.

        Arguments:
          file: An open file object containing a .tar.gz archive.
          uploader: The user who uploaded this package archive.

        Returns: Both the Package object and the PackageVersion object.
        """
        try:
            tar = tarfile.open(mode="r:gz", fileobj=file)
            changelog = Readme.from_archive(tar, name='CHANGELOG')
            readme = Readme.from_archive(tar)
            pubspec = Pubspec.from_archive(tar)
            name = pubspec.required('name')
            package = Package.get_by_key_name(name)
            if not package:
                assert uploader is not None
                package = Package.new(name=name, uploaders=[uploader])

            libraries = sorted(name[4:] for name in tar.getnames()
                               if name.startswith('lib/') and
                                   not name.startswith('lib/src/') and
                                   name.endswith('.dart'))

            return PackageVersion.new(
                package=package, changelog=changelog, readme=readme, 
                pubspec=pubspec, libraries=libraries, uploader=uploader)
        except (tarfile.TarError, KeyError) as err:
            raise db.BadValueError(
                "Error parsing package archive: %s" % err)

    @classmethod
    def get_by_name_and_version(cls, package_name, version):
        """Looks up a package version by its package name and version."""
        parent_key = db.Key.from_path('Package', package_name)
        return cls.get_by_key_name(
            SemanticVersion(version).canonical, parent=parent_key)

    @classmethod
    def get_reload_status(cls):
        """Returns the status of the current package reload.

        This is a map with keys 'total' and 'count', indicating the total number
        of packages to reload and the number that have been reloaded so far,
        respectively.

        If the reload has already completed, or no reload has been started, this
        will return None.
        """
        versions_reloaded = memcache.get('versions_reloaded')
        versions_to_reload = memcache.get('versions_to_reload')
        if versions_to_reload is None: return
        if versions_reloaded is None: return
        if versions_to_reload == versions_reloaded: return
        return {'total': versions_to_reload, 'count': versions_reloaded}

    @property
    def short_created(self):
        """The short created time of the package version."""
        return self.created.strftime('%b %d, %Y')

    @property
    def download_url(self):
        """The URL for downloading this package."""
        return cloud_storage.object_url(self.storage_path)

    @property
    def has_libraries(self):
        """Whether the package version has any libraries at all."""
        return bool(self.libraries)

    @property
    def import_examples(self):
        """The import examples to display for this package version.

        If the version has a library that has the same name as the package,
        that's considered to be the primary library and is the only one shown.
        Otherwise, it will show all the top-level libraries. Only if there are
        no top-level libraries will it show nested libraries.
        """

        primary_library = self.package.name + '.dart'
        if primary_library in self.libraries:
            return self._import_for_library(primary_library)

        top_level = [self._import_for_library(library)
                     for library in self.libraries
                     if not '/' in library]
        if top_level: return top_level

        return map(self._import_for_library, self.libraries)

    def _import_for_library(self, library):
        """Return the import information for a library in this package."""
        return {'package': self.package.name, 'library': library}

    @property
    def example_version_constraint(self):
        """Return the example version constraint for this package."""
        if self.version.in_initial_development:
            return json.dumps(">=%s <%d.%d.0" % 
                (self.version, self.version.major, self.version.minor + 1))
        return json.dumps(
            ">=%s <%d.0.0" % (self.version, self.version.major + 1))

    @property
    def storage_path(self):
        """The Cloud Storage path for this package."""
        # Use the canonical version for the cloud storage path for
        # backwards-compatibility with package versions that were uploaded
        # prior to storing non-canonicalized versions.
        return 'packages/%s-%s.tar.gz' % \
            (self.package.name, self.version.canonical)

    @property
    def dartdoc_storage_path(self):
        """The Cloud Storage path for this package's dartdoc."""
        return 'packages/%s-%s/dartdoc.json' % (self.package.name, self.version)

    def _validate_fields_match_pubspec(self):
        """Assert that the fields in the pubspec match this object's fields."""

        name_in_pubspec = self.pubspec.required('name')
        if name_in_pubspec != self.package.name:
            raise db.BadValueError(
                'Name "%s" in pubspec doesn\'t match package name "%s"' %
                (name_in_pubspec, self.package.name))

        version_in_pubspec = SemanticVersion(self.pubspec.required('version'))
        if version_in_pubspec != self.version:
            raise db.BadValueError(
                'Version "%s" in pubspec doesn\'t match version "%s"' %
                (version_in_pubspec._key(), self.version._key()))
    @property
    def url(self):
        """The API URL for this package version."""
        return models.url(controller='api.versions',
                          action='show',
                          package_id=self.package.name,
                          id=str(self.version))

    def as_dict(self, full=False):
        """Returns the dictionary representation of this package version.

        This is used to represent the package in API responses. Normally this
        just includes URLs and the pubspec, but if full is True, it will include
        all available information about the package version.
        """

        value = {
            'version': str(self.version),
            'url': self.url,
            'package_url': models.url(controller='api.packages',
                                      action='show',
                                      id=self.package.name),
            'new_dartdoc_url': self.url + '/new_dartdoc',
            'archive_url': models.url(controller='versions',
                                      action='show',
                                      package_id=self.package.name,
                                      id=str(self.version),
                                      format='tar.gz'),
            'pubspec': self.pubspec
        }

        if full:
            value.update({
                'created': self.created.isoformat(),
                'downloads': self.downloads,
                'libraries': self.libraries,
                'uploader': self.uploader.email()
            })

        return value
