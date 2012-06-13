# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from google.appengine.ext import db

from testcase import TestCase
from models.package import Package

class PackageVersionTest(TestCase):
    def testVersionMatchesSemver(self):
        package = Package.new(name='test-package', owner=self.adminUser())
        package.put()

        def assertValidSemver(version):
            # This just shouldn't raise an error
            self.packageVersion(package, version)

        def assertInvalidSemver(version):
            self.assertRaises(
                db.BadValueError,
                lambda: self.packageVersion(package, version))

        assertValidSemver("0.0.0")
        assertValidSemver("12.34.56")
        assertValidSemver("1.2.3-alpha.1")
        assertValidSemver("1.2.3+x.7.z-92")
        assertValidSemver("1.0.0-rc-1+build-1")

        assertInvalidSemver("1.0")
        assertInvalidSemver("1.2.3.4")
        assertInvalidSemver("1234")
        assertInvalidSemver("-2.3.4")
        assertInvalidSemver("1.3-pre")
        assertInvalidSemver("1.3+build")
        assertInvalidSemver("1.3+bu?!3ild")
