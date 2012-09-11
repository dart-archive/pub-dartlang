# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from testcase import TestCase
from models.package import Package

class PackageTest(TestCase):
    def testExists(self):
        Package.new(name='test-package', owner=self.adminUser()).put()

        self.assertTrue(Package.exists('test-package'))
        self.assertFalse(Package.exists('other-package'))

    def testHasVersion(self):
        package = Package.new(name='test-package', owner=self.adminUser())
        package.put()
        self.packageVersion(package, '1.2.3').put()

        self.assertTrue(package.has_version('1.2.3'))
        self.assertFalse(package.has_version('1.2.4'))

    def testDescription(self):
        package = Package.new(name='test-package', owner=self.adminUser())
        package.put()

        def get_description():
            return Package.get_by_key_name(package.name).description

        def set_latest_version(version, **additional_pubspec_fields):
            version = self.packageVersion(
                package, version, **additional_pubspec_fields)
            package.latest_version = version
            version.put()
            package.put()

        self.assertIsNone(get_description())

        set_latest_version('1.2.3')
        self.assertIsNone(get_description())

        set_latest_version('1.2.4', description='some package')
        self.assertEquals('some package', get_description())
