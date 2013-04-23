# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from testcase import TestCase

import handlers
from models.package import Package
from models.package_version import PackageVersion

class RootTest(TestCase):
    def test_in_production_is_false_in_tests(self):
        # A little sanity check to make sure the tests don't run against
        # production.
        self.assertFalse(handlers.is_production())

    def test_index_lists_recent_packages_in_update_order(self):
        self.be_admin_user()

        packages = [
            'armadillo', 'bat', 'crocodile', 'dragon', 'elephant', 'frog',
            'gorilla', 'headcrab'
        ]

        for package in packages:
            self.create_package(package, '1.0.0')

        # Update a package so the update times are different from create times.
        self.set_latest_version('bat', '1.0.1')

        # Only the five most recent packages should be listed
        self.assert_list_in_html('/', 'tbody tr th',
            ['bat', 'headcrab', 'gorilla', 'frog', 'elephant'])

    def test_admin_requires_login(self):
        response = self.testapp.get('/admin')
        self.assert_requires_login(response)

    def test_admin_requires_admin(self):
        self.be_normal_user()
        response = self.testapp.get('/admin', status=403)
        self.assert_error_page(response)
