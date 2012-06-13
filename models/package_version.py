# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import re
import tarfile

from google.appengine.ext import db
import yaml

from package import Package
from properties import DocumentProperty

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

    pubspec = DocumentProperty(required=True, indexed=False)

    package = db.ReferenceProperty(Package,
                                   required=True,
                                   collection_name = "version_set")
    """The Package model for this package version."""

    def __init__(self, *args, **kwargs):
        """Construct a new package version.

        This automatically sets the key name of the model. Unless the key is set
        explicitly, it requires that the version and package keys be passed in.
        """

        if 'contents_file' in kwargs:
            kwargs['pubspec'] = self._parse_contents(kwargs['contents_file'])
            kwargs['contents'] = db.Blob(kwargs['contents_file'].read())

            kwargs['version'] = self._required_pubspec_value(
                kwargs['pubspec'], 'version')
            name_in_pubspec = self._required_pubspec_value(
                kwargs['pubspec'], 'name')
            if name_in_pubspec != kwargs['package'].name:
                raise db.BadValueError(
                    'Name "%s" in pubspec doesn\'t match package name "%s"' %
                    (name_in_pubspec, kwargs['package'].name))

        if not 'key_name' in kwargs and not 'key' in kwargs:
            kwargs['key_name'] = \
                "%s %s" % (kwargs['package'].name, kwargs['version'])

        super(PackageVersion, self).__init__(*args, **kwargs)

    @classmethod
    def get_by_name_and_version(cls, package_name, version):
        """Looks up a package version by its package name and version."""
        return cls.get_by_key_name("%s %s" % (package_name, version))

    @property
    def download_url(self):
        """The URL for downloading this package."""
        return "/packages/%s/versions/%s.tar.gz" % \
            (self.package.name, self.version)

    def _parse_contents(self, file):
        """Extract and return the parsed pubspec from the package archive.

        After consuming the file, this puts the cursor back at the beginning."""
        try:
            tar = tarfile.open(mode="r:gz", fileobj=file)
            pubspec = yaml.load(tar.extractfile("pubspec.yaml").read())
            if not isinstance(pubspec, dict):
                raise db.BadValueError(
                    "Invalid pubspec, expected mapping at top level, was %s" %
                    pubspec)
            file.seek(0)
            return pubspec
        except (tarfile.TarError, KeyError) as err:
            raise db.BadValueError(
                "Error parsing package archive: %s" % err)
        except yaml.YAMLError as err:
            raise db.BadValueError("Error parsing pubspec: %s" % err)

    def _required_pubspec_value(self, pubspec, key):
        """Assert a value in the pubspec exists and return it."""
        if key not in pubspec:
            raise db.BadValueError("Pubspec is missing key %r" % key)
        return pubspec[key]
