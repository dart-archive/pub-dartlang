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
