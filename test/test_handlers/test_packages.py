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

        form['file'] = ('test-package-0.0.1.tar.gz', self.tarPubspec({
                'name': 'test-package',
                'version': '0.0.1'
            }))
        post_response = form.submit()

        self.assertEqual(post_response.status_int, 302)
        self.assertEqual(post_response.headers['Location'],
                         'http://localhost:80/packages/test-package')
        self.assertTrue(post_response.cookies_set.has_key('flash'))

        package = Package.get_by_key_name('test-package')
        self.assertTrue(package is not None)
        self.assertEqual(package.name, 'test-package')
        self.assertEqual(package.owner, users.get_current_user())

        version = package.version_set.get()
        self.assertTrue(version is not None)
        self.assertEqual(version.version, '0.0.1')
        self.assertEqual(version.package.name, 'test-package')

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
        upload = self.uploadArchive('test-package', '0.0.1')
        response = self.testapp.post(
            '/packages', upload_files=[upload], status=403)
        self.assertErrorPage(response)

    def testCreateRequiresAdmin(self):
        self.beNormalUser()

        upload = self.uploadArchive('test-package', '0.0.1')
        response = self.testapp.post(
            '/packages', upload_files=[upload], status=403)
        self.assertErrorPage(response)

    def testCreateRequiresNewPackageName(self):
        self.beAdminUser()

        other_admin = self.adminUser('other')
        Package.new(name='test-package', owner=other_admin).put()

        upload = self.uploadArchive('test-package', '0.0.1')
        response = self.testapp.post('/packages', upload_files=[upload])
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost:80/packages/new')
        self.assertTrue(response.cookies_set.has_key('flash'))

        package = Package.get_by_key_name('test-package')
        self.assertEqual(package.owner, other_admin)

    def testIndexListsPackagesInUpdateOrder(self):
        self.beAdminUser()

        Package.new(name='armadillo').put()
        Package.new(name='zebra').put()
        mongoose = Package.new(name='mongoose')
        mongoose.put()
        Package.new(name='snail').put()

        # Make update time different than create time
        mongoose.put()

        self.expectListsPackages(['mongoose', 'snail', 'zebra', 'armadillo'])

    def testIndexListsOnePageOfPackages(self):
        self.beAdminUser()

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
        self.expectListsPackages([
                'llama', 'kangaroo', 'jaguar', 'ibex', 'headcrab', 'gorilla',
                'frog', 'elephant', 'dragon', 'crocodile'])

    def testGetNonExistantPackage(self):
        self.testapp.get('/packages/package/test-package', status=404)

    def testGetUnownedPackage(self):
        self.beAdminUser()
        Package.new(name='test-package').put()

        self.beNormalUser()
        response = self.testapp.get('/packages/test-package')
        self.assertNoLink(response, '/packages/test-package/versions/new')

    def testGetOwnedPackage(self):
        self.beAdminUser()
        Package.new(name='test-package').put()

        response = self.testapp.get('/packages/test-package')
        self.assertLink(response, '/packages/test-package/versions/new')

    def testGetPackageJsonWithoutVersions(self):
        admin = self.adminUser()
        Package.new(name='test-package', owner=admin).put()

        response = self.testapp.get('/packages/test-package.json')
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(json.loads(response.body), {
            "name": "test-package",
            "owner": admin.email(),
            "versions": []
        })

    def testGetPackageJsonWithVersions(self):
        admin = self.adminUser()
        package = Package.new(name='test-package', owner=admin)
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
        
