# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from google.appengine.api import users

from testcase import TestCase
from models.package import Package

class PackagesTest(TestCase):
    def testAdminCreatesPackage(self):
        self.beAdminUser()

        get_response = self.testapp.get('/packages/create')
        self.assertEqual(get_response.status_int, 200)
        form = get_response.form
        self.assertEqual(form.action, '/packages/')
        self.assertEqual(form.method, 'POST')

        form['name'] = 'test-package'
        post_response = form.submit()

        self.assertEqual(post_response.status_int, 302)
        self.assertEqual(post_response.headers['Location'],
                         'http://localhost:80/packages/')
        self.assertTrue(post_response.cookies_set.has_key('flash'))

        package = Package.get_by_key_name('test-package')
        self.assertTrue(package is not None)
        self.assertEqual(package.name, 'test-package')
        self.assertEqual(package.owner, users.get_current_user())

    def testGetCreateRequiresLogin(self):
        response = self.testapp.get('/packages/create')
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers['Location'],
                         'https://www.google.com/accounts/Login?continue=http'
                         '%3A//localhost%3A80/packages/create')

    def testGetCreateRequiresAdmin(self):
        self.beNormalUser()

        response = self.testapp.get('/packages/create')
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost:80/packages/')
        self.assertTrue(response.cookies_set.has_key('flash'))

    def testPostPackagesRequiresLogin(self):
        response = self.testapp.post('/packages/', {'name': 'test-package'},
                                     status=403)
        self.assertErrorPage(response)

    def testPostPackagesRequiresAdmin(self):
        self.beNormalUser()

        response = self.testapp.post('/packages/', {'name': 'test-package'},
                                     status=403)
        self.assertErrorPage(response)

    def testPostPackagesRequiresNewPackageName(self):
        self.beAdminUser()

        other_admin = self.adminUser('other')
        Package(name='test-package', owner=other_admin).put()

        response = self.testapp.post('/packages/', {'name': 'test-package'})
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost:80/packages/create')
        self.assertTrue(response.cookies_set.has_key('flash'))

        package = Package.get_by_key_name('test-package')
        self.assertEqual(package.owner, other_admin)

    def testGetPackagesListsPackagesInUpdateOrder(self):
        self.beAdminUser()

        Package(name='armadillo').put()
        Package(name='zebra').put()
        mongoose = Package(name='mongoose')
        mongoose.put()
        Package(name='snail').put()

        # Make update time different than create time
        mongoose.put()

        self.expectListsPackages(['mongoose', 'snail', 'zebra', 'armadillo'])

    def testGetPackagesListsOnePageOfPackages(self):
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

    def expectListsPackages(self, expected_order):
        """Assert that the package index lists packages in a particular order.

        Arguments:
          expected_order: A list of package names.
        """
        response = self.testapp.get('/packages/')
        for li in self.html(response).select("#packages li"):
            if not expected_order:
                self.fail("more packages were listed than expected: %s" % li)
            elif expected_order[0] in li.string:
                del expected_order[0]
            else:
                self.fail("expected package '%s' in element %s" %
                          (expected_order[0], li))

        self.assertEqual(expected_order, [],
                         "<li>s not found for packages: %s" % expected_order)
        
