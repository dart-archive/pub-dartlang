# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from testcase import TestCase
from models.package import Package

class PackageTest(TestCase):
    def test_exists(self):
        Package.new(name='test-package', uploaders=[self.admin_user()]).put()

        self.assertTrue(Package.exists('test-package'))
        self.assertFalse(Package.exists('other-package'))

    def test_has_version(self):
        package = Package.new(name='test-package',
                              uploaders=[self.admin_user()])
        package.put()
        self.package_version(package, '1.2.3').put()

        self.assertTrue(package.has_version('1.2.3'))
        self.assertFalse(package.has_version('1.2.4'))

    def test_description(self):
        package = Package.new(name='test-package',
                              uploaders=[self.admin_user()])
        package.put()

        def get_description():
            return Package.get_by_key_name(package.name).description

        def set_latest_version(version, **additional_pubspec_fields):
            version = self.package_version(
                package, version, **additional_pubspec_fields)
            package.latest_version = version
            version.put()
            package.put()

        self.assertIsNone(get_description())

        set_latest_version('1.2.3')
        self.assertIsNone(get_description())

        set_latest_version('1.2.4', description='some package')
        self.assertEquals('some package', get_description())
