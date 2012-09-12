# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import itertools
from google.appengine.ext import db

from testcase import TestCase
from models.semantic_version import SemanticVersion

class SemanticVersionTest(TestCase):
    def test_version_matches_semver(self):
        def assert_valid_semver(version):
            self.assertEqual(version, str(SemanticVersion(version)))

        def assert_invalid_semver(version):
            self.assertRaises(
                db.BadValueError,
                lambda: SemanticVersion(version))

        assert_valid_semver("0.0.0")
        assert_valid_semver("12.34.56")
        assert_valid_semver("1.2.3-alpha.1")
        assert_valid_semver("1.2.3+x.7.z-92")
        assert_valid_semver("1.0.0-rc-1+build-1")

        assert_invalid_semver("1.0")
        assert_invalid_semver("1.2.3.4")
        assert_invalid_semver("1234")
        assert_invalid_semver("-2.3.4")
        assert_invalid_semver("1.3-pre")
        assert_invalid_semver("1.3+build")
        assert_invalid_semver("1.3+bu?!3ild")

    def test_ordering(self):
        def assert_less_than(version1, version2):
            self.assertTrue(
                SemanticVersion(version1) < SemanticVersion(version2),
                "Expected %s < %s" % (version1, version2))

        # These version numbers come from the semantic versioning spec, located
        # at http://semver.org/.
        versions = ["1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-beta.2",
                    "1.0.0-beta.11", "1.0.0-rc.1", "1.0.0-rc.1+build.1",
                    "1.0.0", "1.0.0+0.3.7", "1.3.7+build",
                    "1.3.7+build.2.b8f12d7", "1.3.7+build.11.e0f985a"]

        for version1, version2 in _pairs(versions):
            assert_less_than(version1, version2)

def _pairs(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.izip(a, b)
