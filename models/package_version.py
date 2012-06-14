# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import re
import tarfile

from google.appengine.ext import db
import yaml

from package import Package
from properties import PubspecProperty
from pubspec import Pubspec

class PackageVersion(db.Model):
    """The model for a single version of a package.

    This model contains the actual (compressed) blob of code for this version of
    the package.
    """

    _SEMANTIC_VERSION_RE = re.compile(r"""
      ^
      (\d+)\.(\d+)\.(\d+)              # Version number.
      (-([0-9a-z-]+(\.[0-9a-z-]+)*))?  # Pre-release.
      (\+([0-9a-z-]+(\.[0-9a-z-]+)*))? # Build.
      $                                # Consume entire string.
      """, re.VERBOSE | re.IGNORECASE)

    def _check_semver(value):
        """Validate that value matches the semantic version spec."""
        if PackageVersion._SEMANTIC_VERSION_RE.match(value): return
        raise db.BadValueError('"%s" is not a valid semantic version.' % value)

    version = db.StringProperty(required=True, validator=_check_semver)
    """The version of the package, a valid semantic version."""

    created = db.DateTimeProperty(auto_now_add=True)
    """When this package version was created."""

    contents = db.BlobProperty(required=True)
    """The blob of code for this package version, a gzipped tar file."""

    pubspec = PubspecProperty(required=True, indexed=False)

    package = db.ReferenceProperty(Package,
                                   required=True,
                                   collection_name = "version_set")
    """The Package model for this package version."""

    @classmethod
    def new(cls, **kwargs):
        """Construct a new package version.

        Unlike __init__, this infers some properties from others. In particular:

        - The pubspec is loaded from contents_file, if provided.
        - The version is inferred from the pubspec.
        - The key name is set to the version.
        - The parent entity is set to the package.
        """

        if 'contents_file' in kwargs:
            file = kwargs['contents_file']
            if 'pubspec' not in kwargs:
                kwargs['pubspec'] = Pubspec.from_archive(file)
            kwargs['contents'] = db.Blob(file.read())

        if 'pubspec' in kwargs and 'version' not in kwargs:
            kwargs['version'] = kwargs['pubspec'].required('version')

        if not 'key_name' in kwargs and not 'key' in kwargs:
            kwargs['key_name'] = kwargs['version']

        if not 'parent' in kwargs:
            kwargs['parent'] = kwargs['package']

        version = cls(**kwargs)
        version._validate_fields_match_pubspec()
        return version

    @classmethod
    def get_by_name_and_version(cls, package_name, version):
        """Looks up a package version by its package name and version."""
        parent_key = db.Key.from_path('Package', package_name)
        return cls.get_by_key_name(version, parent=parent_key)

    @property
    def download_url(self):
        """The URL for downloading this package."""
        return "/packages/%s/versions/%s.tar.gz" % \
            (self.package.name, self.version)

    def _validate_fields_match_pubspec(self):
        """Assert that the fields in the pubspec match this object's fields."""

        name_in_pubspec = self.pubspec.required('name')
        if name_in_pubspec != self.package.name:
            raise db.BadValueError(
                'Name "%s" in pubspec doesn\'t match package name "%s"' %
                (name_in_pubspec, self.package.name))

        version_in_pubspec = self.pubspec.required('version')
        if version_in_pubspec != self.version:
            raise db.BadValueError(
                'Version "%s" in pubspec doesn\'t match version "%s"' %
                (name_in_pubspec, self.version))
