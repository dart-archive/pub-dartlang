# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from testcase import TestCase

from models.package import Package

class RootTest(TestCase):
    def test_index_lists_recent_packages_in_update_order(self):
        self.be_admin_user()

        packages = ['armadillo', 'bat', 'crocodile', 'dragon', 'elephant',
            'frog', 'gorilla', 'headcrab'
        ]

        for package in packages:
            Package.new(name=package).put()

        # Only the five most recent packages should be listed
        self.assert_list_in_html('/', 'tbody tr th', packages[:5])
