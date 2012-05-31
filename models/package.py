# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from google.appengine.ext import db

class Package(db.Model):
    """The model for a package.

    A package contains only metadata that applies to every version of the
    package, such as its name and owner. Each individual version of the package
    is represented by a PackageVersion model.
    """

    owner = db.UserProperty(auto_current_user_add=True)
    """The user who owns the package."""

    name = db.StringProperty(required=True)
    """The name of the package."""

    created = db.DateTimeProperty(auto_now_add=True)
    """When the package was created."""

    updated = db.DateTimeProperty(auto_now=True)
    """When the package or any of its versions were last updated."""

    def __init__(self, *args, **kwargs):
        """Construct a new package.

        This automatically sets the key name of the model to the name field,
        in order to ensure that each package has a unique name.
        """
        kwargs['key_name'] = kwargs['name']
        super(Package, self).__init__(*args, **kwargs)

    @classmethod
    def exists(cls, name):
        """Determine whether a package with the given name exists."""
        return cls.get_by_key_name(name) is not None
