# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import cgi
import json
import logging

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db

import models
from pubspec import Pubspec

class Package(db.Model):
    """The model for a package.

    A package contains only metadata that applies to every version of the
    package, such as its name and uploader. Each individual version of the
    package is represented by a PackageVersion model.

    Whenever a new PackageVersion for a Package is added or modified, you must
    call invalidate_cache() to ensure any stale cached description of the
    package is discarded.
    """

    MAX_SIZE = 10 * 2**20 # 10MB
    """The maximum package size, in bytes."""

    uploaders = db.ListProperty(users.User, validator=models.validate_not_empty)
    """The users who are allowed to upload new versions of the package.

    When this is set, invalidate_cache() must be called."""

    name = db.StringProperty(required=True)
    """The name of the package."""

    created = db.DateTimeProperty(auto_now_add=True)
    """When the package was created."""

    downloads = db.IntegerProperty(required=True, default=0)
    """The number of times any version of this package has been downloaded."""

    # This should only reference a PackageVersion, but cyclic imports aren't
    # allowed so we can't import PackageVersion here.
    latest_version = db.ReferenceProperty()
    """The most recent non-prerelease version of this package.

    When this is set, invalidate_cache() must be called."""

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
    def documentation(self):
        """The documentation URL for the package, or None."""
        if self.latest_version is None: return None
        return self.latest_version.pubspec.get('documentation',
            'http://www.dartdocs.org/documentation/%s/%s/index.html#%s' % \
            (self.name, self.latest_version.version, self.name))

    @property
    def authors_title(self):
        """The title for the authors list of the package."""
        return 'Author' if len(self.latest_version.pubspec.authors) == 1 \
            else 'Authors'

    @property
    def authors_html(self):
        """Inline HTML for the authors of this package."""
        if self.latest_version is None: return ''

        def author_html((author, email)):
            if email is None: return cgi.escape(author)
            return '''<span class="author">
                <a href="mailto:%s" title="Email %s">
                    <i class="icon-envelope">Email %s</i>
                </a> %s</span>''' % \
                (cgi.escape(email), cgi.escape(email),
                 cgi.escape(email), cgi.escape(author))

        return '<br/>'.join(map(author_html, self.latest_version.pubspec.authors))

    @property
    def uploaders_title(self):
        """The title for the uploaders list of the package."""
        return 'Uploader' if len(self.latest_version.pubspec.authors) == 1 \
            else 'Uploaders'

    @property
    def uploaders_html(self):
        """Inline HTML for the uploaders of this package."""
        return '<br/>'.join(cgi.escape(uploader.nickname())
                         for uploader in self.uploaders)

    @property
    def short_updated(self):
        """The short updated time of the package."""
        return self.updated.strftime('%b %d, %Y')

    @classmethod
    def new(cls, **kwargs):
        """Construct a new package.

        Unlike __init__, this infers some properties from others. In particular:

        - The key name is inferred from the package name.
        """

        if not 'key_name' in kwargs and not 'key' in kwargs:
            kwargs['key_name'] = kwargs['name']

        return cls(**kwargs)

    @db.ComputedProperty
    def updated(self):
        """When the latest version of this package was uploaded.

        This only counts latest_version; pre-release versions and older versions
        will not affect this field."""
        return self.latest_version and self.latest_version.created

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

    def has_uploader(self, uploader):
        """Determine whether the given user is an uploader for this package.

        This compares users via case-insensitive email comparison.

        Although admins have uploader privileges for all packages, this will not
        return True for admins.
        """
        return uploader.email().lower() in \
            [u.email().lower() for u in self.uploaders]

    @property
    def url(self):
        """The API URL for this package."""
        return models.url(
            controller='api.packages', action='show', id=self.name)

    def as_dict(self, full=False):
        """Returns the dictionary representation of this package.

        This is used to represent the package in API responses. Normally this
        just includes URLs and some information about the latest version, but if
        full is True, it will include all available information about the
        package.
        """

        value = {
            'name': self.name,
            'url': self.url,
            'uploaders_url': self.url + '/uploaders',
            'version_url': self.url + '/versions/{version}',
            'new_version_url': self.url + '/versions/new',
            'latest': self.latest_version and self.latest_version.as_dict()
        }

        if full:
            value.update({
                'created': self.created.isoformat(),
                'downloads': self.downloads,
                'uploaders': [uploader.email() for uploader in self.uploaders],
                'versions': [version.as_dict() for version in self.version_set]
            })

        return value

    def as_json(self):
        """Returns the JSON stringified representation of the full information
        for this package.
        """
        cached = memcache.get(self._package_json_cache_key)
        if cached:
            logging.info("Found cached " + self._package_json_cache_key)
            return cached

        value = json.dumps(self.as_dict(full=True))
        memcache.set(self._package_json_cache_key, value)
        return value

    def invalidate_cache(self):
        """Clears the cached JSON for the package.

        This must be called any time any data that is in the JSON for the full
        description of the package changes. This isn't often since most package
        data is immutable, but when the uploader list changes or new versions
        of the package are uploaded, the data will change.
        """
        memcache.delete(self._package_json_cache_key)

    @property
    def _package_json_cache_key(self):
        """The memcache key for the cached JSON for this package."""
        return 'package_json_' + self.name
