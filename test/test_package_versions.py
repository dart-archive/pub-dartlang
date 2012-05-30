# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from testcase import TestCase
from models.package import Package

class PackageVersionsTest(TestCase):
    def setUp(self):
        super(PackageVersionsTest, self).setUp()
        Package(name='test-package', owner=self.adminUser()).put()

    def testNewRequiresLogin(self):
        response = self.testapp.get('/packages/test-package/versions/new')
        self.assertRequiresLogin(response)

    def testNewRequiresOwnership(self):
        self.beNormalUser()

        response = self.testapp.get('/packages/test-package/versions/new')
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost:80/packages/test-package')
        self.assertTrue(response.cookies_set.has_key('flash'))
