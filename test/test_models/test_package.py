# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from testcase import TestCase
from models.package import Package
from models.package_version import PackageVersion

class PackageTest(TestCase):
    def testExists(self):
        Package(name='test-package', owner=self.adminUser()).put()

        self.assertTrue(Package.exists('test-package'))
        self.assertFalse(Package.exists('other-package'))

    def testHasVersion(self):
        package = Package(name='test-package', owner=self.adminUser())
        package.put()
        PackageVersion(version='1.2.3', package=package, contents='foo').put()

        self.assertTrue(package.has_version('1.2.3'))
        self.assertFalse(package.has_version('1.2.4'))
