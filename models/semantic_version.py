# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import re
from functools import total_ordering

from google.appengine.ext import db

@total_ordering
class SemanticVersion(object):
    """A semantic version number. See http://semver.org/."""

    _RE = re.compile(r"""
      ^
      (\d+)\.(\d+)\.(\d+)                  # Version number.
      (?:-([0-9a-z-]+(?:\.[0-9a-z-]+)*))?  # Pre-release.
      (?:\+([0-9a-z-]+(?:\.[0-9a-z-]+)*))? # Build.
      $                                    # Consume entire string.
      """, re.VERBOSE | re.IGNORECASE)

    def __init__(self, version):
        """Parse a semantic version string."""

        match = SemanticVersion._RE.match(version)
        if not match: raise db.BadValueError(
            '"%s" is not a valid semantic version.' % version)

        self.major = int(match.group(1))
        self.minor = int(match.group(2))
        self.patch = int(match.group(3))
        self.prerelease = _split(match.group(4))
        self.build = _split(match.group(5))

    @property
    def is_prerelease(self):
        """Whether this is a prerelease version."""
        return self.prerelease is not None

    def __eq__(self, other):
        if not isinstance(other, SemanticVersion): return False
        return self._key() == other._key()

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self._key() < other._key()

    def _key(self):
        """The key to use for equality and ordering comparisons."""
        return (self.major, self.minor, self.patch, self.prerelease, self.build)

    def __str__(self):
        prerelease = ""
        if self.prerelease:
            prerelease = "-" + '.'.join(map(str, self.prerelease))

        build = ""
        if self.build: build = "+" + '.'.join(map(str, self.build))

        return "%d.%d.%d%s%s" % (self.major, self.minor, self.patch, prerelease,
                                 build)

    def __repr__(self):
        return 'SemanticVersion({0!r})'.format(str(self))

def _split(string):
    """Split a prerelease or build string as per the semver spec.

    Specifically, splits the string on periods, then converts every section that
    contains only numeric digits to an integer.
    """

    if string is None: return
    def maybe_make_int(substring):
        if re.search(r'[^0-9]', substring): return substring
        return int(substring)
    return map(maybe_make_int, string.split('.'))
