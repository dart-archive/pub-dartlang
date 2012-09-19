# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import cgi

from google.appengine.ext import db

import models
from pubspec import Pubspec

class Package(db.Model):
    """The model for a package.

    A package contains only metadata that applies to every version of the
    package, such as its name and uploader. Each individual version of the
    package is represented by a PackageVersion model.
    """

    # TODO(nweiz): This should more properly be called "uploader". Change the
    # name once we support multiple uploaders for each package.
    owner = db.UserProperty(required=True, auto_current_user_add=True)
    """The user who is allowed to upload new versions of the package."""

    name = db.StringProperty(required=True)
    """The name of the package."""

    created = db.DateTimeProperty(auto_now_add=True)
    """When the package was created."""

    updated = db.DateTimeProperty(auto_now=True)
    """When the package or any of its versions were last updated."""

    # This should only reference a PackageVersion, but cyclic imports aren't
    # allowed so we can't import PackageVersion here.
    latest_version = db.ReferenceProperty()
    """The most recent non-prerelease version of this package."""

    @property
    def description(self):
        """The short description of the package."""
        if self.latest_version is None: return None
        return self.latest_version.pubspec.get('description')

    _MAX_DESCRIPTION_CHARS = 200

    @property
    def ellipsized_description(self):
        """The short description of the package, truncated if necessary."""
        description = self.description
        if description is None: return None
        return models.ellipsize(description, Package._MAX_DESCRIPTION_CHARS)

    @property
    def homepage(self):
        """The home page URL for the package, or None."""
        if self.latest_version is None: return None
        return self.latest_version.pubspec.get('homepage')

    @property
    def authors_html(self):
        """Inline HTML for the authors of this package."""
        if self.latest_version is None: return ''

        def author_html((author, email)):
            if email is None: return cgi.escape(author)
            return '<a href="mailto:%s">%s</a>' % \
                (cgi.escape(email), cgi.escape(author))

        return ', '.join(map(author_html, self.latest_version.pubspec.authors))

    @classmethod
    def new(cls, **kwargs):
        """Construct a new package.

        Unlike __init__, this infers some properties from others. In particular:

        - The key name is inferred from the package name.
        """

        if not 'key_name' in kwargs and not 'key' in kwargs:
            kwargs['key_name'] = kwargs['name']

        return cls(**kwargs)

    @classmethod
    def from_archive(cls, file):
        """Load a package and a package version from a .tar.gz archive.

        Arguments:
          file: An open file object containing a .tar.gz archive.

        Returns: Both the Package object and the PackageVersion object.
        """
        from package_version import PackageVersion
        pubspec = Pubspec.from_archive(file)
        package = Package.new(name=pubspec.required('name'))
        version = PackageVersion.new(
            package=package, pubspec=pubspec, contents_file=file)
        return package, version

    @classmethod
    def exists(cls, name):
        """Determine whether a package with the given name exists."""
        return cls.get_by_key_name(name) is not None

    def has_version(self, version):
        """Determine whether this package has a given version uploaded."""
        from package_version import PackageVersion
        version = PackageVersion.get_by_name_and_version(
            self.name, str(version))
        return version is not None
