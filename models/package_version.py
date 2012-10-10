# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import copy
import json
import tarfile

from google.appengine.ext import db
import yaml

from semantic_version import SemanticVersion
from handlers import cloud_storage
from package import Package
from properties import PubspecProperty, VersionProperty
from pubspec import Pubspec

class PackageVersion(db.Model):
    """The model for a single version of a package.

    This model contains the actual (compressed) blob of code for this version of
    the package.
    """

    version = VersionProperty(required=True)
    """The version of the package."""

    created = db.DateTimeProperty(auto_now_add=True)
    """When this package version was created."""

    pubspec = PubspecProperty(required=True, indexed=False)
    """The package version's pubspec file."""

    libraries = db.ListProperty(str)
    """All libraries that can be imported from this package version."""

    package = db.ReferenceProperty(Package,
                                   required=True,
                                   collection_name = "version_set")
    """The Package model for this package version."""

    sort_order = db.IntegerProperty(default=-1)
    """The sort order for this version.

    Lower numbers indicate earlier versions."""

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
            kwargs['key_name'] = str(kwargs['version'])

        if not 'parent' in kwargs:
            kwargs['parent'] = kwargs['package']

        version = cls(**kwargs)
        version._validate_fields_match_pubspec()
        return version

    @classmethod
    def from_archive(cls, file):
        """Load a package version from a .tar.gz archive.

        If the package specified in the archive already exists, it will be
        loaded and assigned as the package version's package. If it doesn't, a
        new package will be created.

        Arguments:
          file: An open file object containing a .tar.gz archive.

        Returns: Both the Package object and the PackageVersion object.
        """
        try:
            tar = tarfile.open(mode="r:gz", fileobj=file)
            pubspec = Pubspec.from_archive(tar)
            name = pubspec.required('name')
            package = Package.get_by_key_name(name)
            if not package: package = Package.new(name=name)

            libraries = sorted(name[4:] for name in tar.getnames()
                               if name.startswith('lib/') and
                                   not name.startswith('lib/src/') and
                                   name.endswith('.dart'))

            return PackageVersion.new(
                package=package, pubspec=pubspec, libraries=libraries)
        except (tarfile.TarError, KeyError) as err:
            raise db.BadValueError(
                "Error parsing package archive: %s" % err)

    @classmethod
    def get_by_name_and_version(cls, package_name, version):
        """Looks up a package version by its package name and version."""
        parent_key = db.Key.from_path('Package', package_name)
        return cls.get_by_key_name(version, parent=parent_key)

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
        if self.version.in_initial_development: return str(self.version)
        return json.dumps(
            ">=%s <%d.0.0" % (self.version, self.version.major + 1))

    @property
    def storage_path(self):
        """The Cloud Storage path for this package."""
        return 'packages/%s-%s.tar.gz' % (self.package.name, self.version)

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
