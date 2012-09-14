# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import re
import tarfile

from google.appengine.ext import db
import yaml

from lib import util

class Pubspec(dict):
    """A parsed pubspec.yaml file."""

    _STRING_FIELDS = ['name', 'version', 'author', 'homepage']
    """Pubspec fields that must be strings if they're defined at all."""

    def __init__(self, *args, **kwargs):
        super(Pubspec, self).__init__(*args, **kwargs)

        if 'author' in self and 'authors' in self:
            raise db.BadValueError(
                'Pubspec cannot contain both "author" and "authors" fields.')

        for field in Pubspec._STRING_FIELDS:
            if field in self and not isinstance(self[field], basestring):
                raise db.BadValueError(
                    'Pubspec field "%s" must be a string, was "%r"' %
                    (field, self[field]))

        if 'authors' in self and not (isinstance(self['authors'], basestring) or
                                      isinstance(self['authors'], list)):
            raise db.BadValueError(
                'Pubspec field "authors" must be a string or list, was "%r"' %
                self['authors'])

    @classmethod
    def from_archive(cls, file):
        """Extract and return the parsed pubspec from a package archive.

        After consuming the file, this puts the cursor back at the beginning.
        """
        try:
            tar = tarfile.open(mode="r:gz", fileobj=file)
            pubspec = yaml.load(tar.extractfile("pubspec.yaml").read())
            if not isinstance(pubspec, dict):
                raise db.BadValueError(
                    "Invalid pubspec, expected mapping at top level, was %s" %
                    pubspec)
            file.seek(0)
            return cls(pubspec)
        except (tarfile.TarError, KeyError) as err:
            raise db.BadValueError(
                "Error parsing package archive: %s" % err)
        except yaml.YAMLError as err:
            raise db.BadValueError("Error parsing pubspec: %s" % err)

    def to_yaml(self):
        """Dump the Pubspec to YAML."""
        # "dict()" causes Yaml to tag the output as a standard Yaml mapping
        # rather than a custom "!!python/object/new:models.pubspec.Pubspec"
        # object.
        #
        # "safe_dump()" causes Yaml to tag unicode objects as standard Yaml
        # strings rather than "!!python/unicode".
        return yaml.safe_dump(dict(self))

    def required(self, key):
        """Return a value from the pubspec, and assert that it exists."""
        if key not in self:
            raise db.BadValueError("Pubspec is missing required key '%s'" % key)
        return self[key]

    @property
    def authors(self):
        """Return a normalized list of authors as (name, email) tuples."""
        if 'author' in self: return [self._parse_author(self['author'])]
        if 'authors' not in self: return []

        authors = self['authors']
        if isinstance(authors, list): return map(self._parse_author, authors)
        return [self._parse_author(authors)]

    _AUTHOR_RE = re.compile(r'^(.*?)(?: <(.*)>)?$')

    def _parse_author(self, name):
        """Parse an author name/email pair.

        Parses 'name <email>' into ('name', 'email') and 'name' into ('name,
        None).
        """
        match = Pubspec._AUTHOR_RE.search(name)
        return (match.group(1), match.group(2))
