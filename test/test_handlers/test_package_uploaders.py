# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from models.package import Package
from testcase import TestCase

class PackageUploadsTest(TestCase):
    def setUp(self):
        super(PackageUploadsTest, self).setUp()
        self.package = Package.new(name='test-package',
                                   uploaders=[self.admin_user()])
        self.package.put()

    def test_create_requires_login(self):
        response = self.testapp.post('/packages/test-package/uploaders.json',
                                     {'email': self.normal_user().email()},
                                     status=403)
        self.assert_json_error(response)

    def test_create_requires_uploader(self):
        self.be_normal_oauth_user()
        response = self.testapp.post('/packages/test-package/uploaders.json',
                                     {'email': self.normal_user().email()},
                                     status=403)
        self.assert_json_error(response)

    def test_uploader_creates_new_uploader(self):
        self.be_admin_oauth_user()
        response = self.testapp.post('/packages/test-package/uploaders.json',
                                     {'email': self.normal_user().email()})
        self.assert_json_success(response)

        package = Package.get_by_key_name('test-package')
        self.assertEquals(
            package.uploaders, [self.admin_user(), self.normal_user()])
