# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from models.package import Package
from testcase import TestCase

class PackageUploadersTest(TestCase):
    def setUp(self):
        super(PackageUploadersTest, self).setUp()
        self.package = Package.new(
            name='test-package',
            uploaders=[self.normal_user('uploader1'),
                       self.normal_user('uploader2')])
        self.package.put()

    def test_create_requires_login(self):
        response = self.testapp.post('/packages/test-package/uploaders.json',
                                     {'email': self.normal_user().email()},
                                     status=401)
        self.assert_json_error(response)

    def test_create_requires_uploader(self):
        self.be_normal_oauth_user()
        response = self.testapp.post('/packages/test-package/uploaders.json',
                                     {'email': self.normal_user().email()},
                                     status=403)
        self.assert_json_error(response)

    def test_create_requires_new_uploader(self):
        self.be_normal_oauth_user('uploader1')
        response = self.testapp.post(
            '/packages/test-package/uploaders.json',
            {'email': self.normal_user('uploader2').email()},
            status=400)
        self.assert_json_error(response)

    def test_uploader_creates_new_uploader(self):
        self.be_normal_oauth_user('uploader1')
        response = self.testapp.post('/packages/test-package/uploaders.json',
                                     {'email': self.normal_user().email()})
        self.assert_json_success(response)

        package = Package.get_by_key_name('test-package')
        self.assertEquals(package.uploaders, [
            self.normal_user('uploader1'),
            self.normal_user('uploader2'),
            self.normal_user()
        ])

    def test_create_is_case_insensitive(self):
        self.be_normal_oauth_user('uploader1')
        response = self.testapp.post(
            '/packages/test-package/uploaders.json',
            {'email': self.normal_user('NAme').email()})
        self.assert_json_success(response)

        response = self.testapp.post(
            '/packages/test-package/uploaders.json',
            {'email': self.normal_user('naME').email()},
            status=400)
        self.assert_json_error(response)

        package = Package.get_by_key_name('test-package')
        self.assertEquals(package.uploaders, [
            self.normal_user('uploader1'),
            self.normal_user('uploader2'),
            self.normal_user('NAme')
        ])

    def test_admin_creates_new_uploader(self):
        self.be_admin_oauth_user()
        response = self.testapp.post('/packages/test-package/uploaders.json',
                                     {'email': self.normal_user().email()})
        self.assert_json_success(response)

        package = Package.get_by_key_name('test-package')
        self.assertEquals(package.uploaders, [
            self.normal_user('uploader1'),
            self.normal_user('uploader2'),
            self.normal_user()
        ])

    def test_delete_requires_login(self):
        response = self.testapp.delete(
            '/packages/test-package/uploaders/%s.json' %
                self.normal_user('uploader1').email(),
            status=401)
        self.assert_json_error(response)

    def test_delete_requires_uploader(self):
        self.be_normal_oauth_user()
        response = self.testapp.delete(
            '/packages/test-package/uploaders/%s.json' %
                self.normal_user('uploader1').email(),
            status=403)
        self.assert_json_error(response)

    def test_cant_delete_non_uploader(self):
        self.be_normal_oauth_user('uploader1')
        response = self.testapp.delete(
            '/packages/test-package/uploaders/%s.json' %
                self.normal_user('non-uploader').email(),
            status=400)
        self.assert_json_error(response)

    def test_cant_delete_only_uploader(self):
        self.package.uploaders = [self.normal_user('uploader1')]
        self.package.put()

        self.be_normal_oauth_user('uploader1')
        response = self.testapp.delete(
            '/packages/test-package/uploaders/%s.json' %
                self.normal_user('uploader1').email(),
            status=400)
        self.assert_json_error(response)

    def test_uploader_deletes_uploader(self):
        self.be_normal_oauth_user('uploader1')
        response = self.testapp.delete(
            '/packages/test-package/uploaders/%s.json' %
                self.normal_user('uploader1').email())
        self.assert_json_success(response)

        package = Package.get_by_key_name('test-package')
        self.assertEquals(
            package.uploaders, [self.normal_user('uploader2')])

    def test_delete_is_case_insensitive(self):
        self.be_normal_oauth_user('uploader1')
        response = self.testapp.delete(
            '/packages/test-package/uploaders/%s.json' %
                self.normal_user('UpLoAdEr1').email())
        self.assert_json_success(response)

        package = Package.get_by_key_name('test-package')
        self.assertEquals(
            package.uploaders, [self.normal_user('uploader2')])

    def test_admin_deletes_uploader(self):
        self.be_admin_oauth_user()
        response = self.testapp.delete(
            '/packages/test-package/uploaders/%s.json' %
                self.normal_user('uploader1').email())
        self.assert_json_success(response)

        package = Package.get_by_key_name('test-package')
        self.assertEquals(
            package.uploaders, [self.normal_user('uploader2')])
