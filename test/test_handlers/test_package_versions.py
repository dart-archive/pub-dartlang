# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from testcase import TestCase
from models.package import Package
from models.package_version import PackageVersion

class PackageVersionsTest(TestCase):
    def setUp(self):
        super(PackageVersionsTest, self).setUp()
        self.package = Package(name='test-package', owner=self.adminUser())
        self.package.put()

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

    def testOwnerCreatesPackageVersion(self):
        self.beAdminUser()

        get_response = self.testapp.get('/packages/test-package/versions/new')
        self.assertEqual(get_response.status_int, 200)
        form = get_response.form
        self.assertEqual(form.action, '/packages/test-package/versions')
        self.assertEqual(form.method, 'POST')

        contents = self.tarPubspec({'name': 'test-package', 'version': '1.2.3'})
        form['file'] = ('test-package-1.2.3.tar.gz', contents)
        post_response = form.submit()

        self.assertEqual(post_response.status_int, 302)
        self.assertEqual(
            post_response.headers['Location'],
            'http://localhost:80/packages/test-package')
        self.assertTrue(post_response.cookies_set.has_key('flash'))

        version = PackageVersion.get_by_key_name('test-package 1.2.3')
        self.assertTrue(version is not None)
        self.assertEqual(version.version, '1.2.3')
        self.assertEqual(version.package.name, 'test-package')

    def testCreateRequiresOwner(self):
        self.beNormalUser()
        upload = self._upload('test-package', '1.2.3')
        response = self.testapp.post(
            '/packages/test-package/versions', upload_files=[upload],
            status=403)
        self.assertErrorPage(response)

    def testCreateRequiresNewVersionNumber(self):
        self.beAdminUser()
        self.packageVersion(self.package, '1.2.3', description='old').put()

        upload = self._upload('test-package', '1.2.3', description='new')
        response = self.testapp.post('/packages/test-package/versions',
                                     upload_files=[upload])
        self.assertEqual(response.status_int, 302)
        self.assertEqual(
            response.headers['Location'],
            'http://localhost:80/packages/test-package/versions/new')
        self.assertTrue(response.cookies_set.has_key('flash'))

        version = PackageVersion.get_by_key_name('test-package 1.2.3')
        self.assertEqual(version.pubspec['description'], 'old')

    def testShowPackageVersionTarGz(self):
        version = self.packageVersion(self.package, '1.2.3')
        version.put()

        response = self.testapp.get(
            '/packages/test-package/versions/1.2.3.tar.gz')
        self.assertEqual(response.headers['Content-Type'],
                         'application/octet-stream')
        self.assertEqual(response.headers['Content-Disposition'],
                         'attachment; filename=test-package-1.2.3.tar.gz')
        self.assertEqual(response.body, self.tarPubspec(version.pubspec))

    def _upload(self, name, version, **additional_pubspec_fields):
        pubspec = {'name': name, 'version': version}
        pubspec.update(additional_pubspec_fields)
        contents = self.tarPubspec(pubspec)
        return ('file', '%s-%s.tar.gz' % (name, version), contents)
