# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import json

from google.appengine.api import users

from testcase import TestCase
from models.package import Package
from models.semantic_version import SemanticVersion

class PackagesTest(TestCase):
    def test_index_lists_packages_in_update_order(self):
        self.be_admin_user()

        Package.new(name='armadillo').put()
        Package.new(name='zebra').put()
        mongoose = Package.new(name='mongoose')
        mongoose.put()
        Package.new(name='snail').put()

        # Make update time different than create time
        mongoose.put()

        self.expect_lists_packages(['mongoose', 'snail', 'zebra', 'armadillo'])

    def test_index_lists_one_page_of_packages(self):
        self.be_admin_user()

        Package.new(name='armadillo').put()
        Package.new(name='bat').put()
        Package.new(name='crocodile').put()
        Package.new(name='dragon').put()
        Package.new(name='elephant').put()
        Package.new(name='frog').put()
        Package.new(name='gorilla').put()
        Package.new(name='headcrab').put()
        Package.new(name='ibex').put()
        Package.new(name='jaguar').put()
        Package.new(name='kangaroo').put()
        Package.new(name='llama').put()

        # Only the ten most recent packages should be listed
        self.expect_lists_packages([
                'llama', 'kangaroo', 'jaguar', 'ibex', 'headcrab', 'gorilla',
                'frog', 'elephant', 'dragon', 'crocodile'])

    def test_get_non_existent_package(self):
        self.testapp.get('/packages/package/test-package', status=404)

    def test_get_unowned_package(self):
        self.be_admin_user()
        Package.new(name='test-package').put()

        self.be_normal_user()
        response = self.testapp.get('/packages/test-package')
        self.assert_no_link(response, '/packages/test-package/versions/new')

    def test_get_owned_package(self):
        self.be_admin_user()
        Package.new(name='test-package').put()

        response = self.testapp.get('/packages/test-package')
        self.assert_link(response, '/packages/test-package/versions/new')

    def test_get_package_json_without_versions(self):
        admin = self.admin_user()
        Package.new(name='test-package', owner=admin).put()

        response = self.testapp.get('/packages/test-package.json')
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(json.loads(response.body), {
            "name": "test-package",
            "owner": admin.email(),
            "versions": []
        })

    def test_get_package_json_with_versions(self):
        admin = self.admin_user()
        package = Package.new(name='test-package', owner=admin)
        package.put()

        self.package_version(package, '1.1.0').put()
        self.package_version(package, '1.1.1').put()
        self.package_version(package, '1.2.0').put()

        response = self.testapp.get('/packages/test-package.json')
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(json.loads(response.body), {
            "name": "test-package",
            "owner": admin.email(),
            "versions": ['1.1.0', '1.1.1', '1.2.0']
        })

    def expect_lists_packages(self, expected_order):
        """Assert that the package index lists packages in a particular order.

        Arguments:
          expected_order: A list of package names.
        """
        response = self.testapp.get('/packages')
        for tr in self.html(response).select("tbody tr"):
            if not expected_order:
                self.fail("more packages were listed than expected: %s" % tr)
            elif expected_order[0] in ''.join(tr.strings):
                del expected_order[0]
            else:
                self.fail("expected package '%s' in element %s" %
                          (expected_order[0], tr))

        self.assertEqual(expected_order, [],
                         "<tr>s not found for packages: %s" % expected_order)
        
