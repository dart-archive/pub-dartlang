# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import json

from google.appengine.api import users

from testcase import TestCase
from models.package import Package

class PackagesTest(TestCase):
    def testAdminCreatesPackage(self):
        self.beAdminUser()

        get_response = self.testapp.get('/packages/new')
        self.assertEqual(get_response.status_int, 200)
        form = get_response.form
        self.assertEqual(form.action, '/packages')
        self.assertEqual(form.method, 'POST')

        form['name'] = 'test-package'
        post_response = form.submit()

        self.assertEqual(post_response.status_int, 302)
        self.assertEqual(post_response.headers['Location'],
                         'http://localhost:80/packages')
        self.assertTrue(post_response.cookies_set.has_key('flash'))

        package = Package.get_by_key_name('test-package')
        self.assertTrue(package is not None)
        self.assertEqual(package.name, 'test-package')
        self.assertEqual(package.owner, users.get_current_user())

    def testNewRequiresLogin(self):
        response = self.testapp.get('/packages/new')
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers['Location'],
                         'https://www.google.com/accounts/Login?continue=http'
                         '%3A//localhost%3A80/packages/new')

    def testNewRequiresAdmin(self):
        self.beNormalUser()

        response = self.testapp.get('/packages/new')
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost:80/packages')
        self.assertTrue(response.cookies_set.has_key('flash'))

    def testCreateRequiresLogin(self):
        response = self.testapp.post('/packages', {'name': 'test-package'},
                                     status=403)
        self.assertErrorPage(response)

    def testCreateRequiresAdmin(self):
        self.beNormalUser()

        response = self.testapp.post('/packages', {'name': 'test-package'},
                                     status=403)
        self.assertErrorPage(response)

    def testCreateRequiresNewPackageName(self):
        self.beAdminUser()

        other_admin = self.adminUser('other')
        Package(name='test-package', owner=other_admin).put()

        response = self.testapp.post('/packages', {'name': 'test-package'})
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost:80/packages/new')
        self.assertTrue(response.cookies_set.has_key('flash'))

        package = Package.get_by_key_name('test-package')
        self.assertEqual(package.owner, other_admin)

    def testIndexListsPackagesInUpdateOrder(self):
        self.beAdminUser()

        Package(name='armadillo').put()
        Package(name='zebra').put()
        mongoose = Package(name='mongoose')
        mongoose.put()
        Package(name='snail').put()

        # Make update time different than create time
        mongoose.put()

        self.expectListsPackages(['mongoose', 'snail', 'zebra', 'armadillo'])

    def testIndexListsOnePageOfPackages(self):
        self.beAdminUser()

        Package(name='armadillo').put()
        Package(name='bat').put()
        Package(name='crocodile').put()
        Package(name='dragon').put()
        Package(name='elephant').put()
        Package(name='frog').put()
        Package(name='gorilla').put()
        Package(name='headcrab').put()
        Package(name='ibex').put()
        Package(name='jaguar').put()
        Package(name='kangaroo').put()
        Package(name='llama').put()

        # Only the ten most recent packages should be listed
        self.expectListsPackages([
                'llama', 'kangaroo', 'jaguar', 'ibex', 'headcrab', 'gorilla',
                'frog', 'elephant', 'dragon', 'crocodile'])

    def testGetNonExistantPackage(self):
        self.testapp.get('/packages/package/test-package', status=404)

    def testGetUnownedPackage(self):
        self.beAdminUser()
        Package(name='test-package').put()

        self.beNormalUser()
        response = self.testapp.get('/packages/test-package')
        self.assertNoLink(response, '/packages/test-package/versions/new')

    def testGetOwnedPackage(self):
        self.beAdminUser()
        Package(name='test-package').put()

        response = self.testapp.get('/packages/test-package')
        self.assertLink(response, '/packages/test-package/versions/new')

    def testGetPackageJsonWithoutVersions(self):
        admin = self.adminUser()
        Package(name='test-package', owner=admin).put()

        response = self.testapp.get('/packages/test-package.json')
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(json.loads(response.body), {
            "name": "test-package",
            "owner": admin.email(),
            "versions": []
        })

    def testGetPackageJsonWithVersions(self):
        admin = self.adminUser()
        package = Package(name='test-package', owner=admin)
        package.put()

        self.packageVersion(package, '1.1.0').put()
        self.packageVersion(package, '1.1.1').put()
        self.packageVersion(package, '1.2.0').put()

        response = self.testapp.get('/packages/test-package.json')
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(json.loads(response.body), {
            "name": "test-package",
            "owner": admin.email(),
            "versions": ['1.1.0', '1.1.1', '1.2.0']
        })

    def expectListsPackages(self, expected_order):
        """Assert that the package index lists packages in a particular order.

        Arguments:
          expected_order: A list of package names.
        """
        response = self.testapp.get('/packages')
        for li in self.html(response).select("#packages li"):
            if not expected_order:
                self.fail("more packages were listed than expected: %s" % li)
            elif expected_order[0] in ''.join(li.strings):
                del expected_order[0]
            else:
                self.fail("expected package '%s' in element %s" %
                          (expected_order[0], li))

        self.assertEqual(expected_order, [],
                         "<li>s not found for packages: %s" % expected_order)
        
