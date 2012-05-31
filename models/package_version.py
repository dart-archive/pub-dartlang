# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from google.appengine.ext import db
from package import Package

class PackageVersion(db.Model):
    """The model for a single version of a package.

    This model contains the actual (compressed) blob of code for this version of
    the package.
    """

    version = db.StringProperty(required=True)
    """The version of the package, a valid semantic version."""

    created = db.DateTimeProperty(auto_now_add=True)
    """When this package version was created."""

    contents = db.BlobProperty(required=True)
    """The blob of code for this package version, a gzipped tar file."""

    package = db.ReferenceProperty(Package,
                                   required=True,
                                   collection_name = "package_version_set")
    """The Package model for this package version."""
