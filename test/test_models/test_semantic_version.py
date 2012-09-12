# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

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
