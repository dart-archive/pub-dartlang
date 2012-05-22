# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from google.appengine.ext import db
from package import Package

class PackageVersion(db.Model):
    version = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    contents = db.BlobProperty()
    package = db.ReferenceProperty(Package,
                                   collection_name = "package_version_set")
