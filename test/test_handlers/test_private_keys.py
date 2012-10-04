# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from testcase import TestCase

from models.private_key import PrivateKey

class PrivateKeysTest(TestCase):
    def test_new_requires_admin(self):
        self.be_normal_user()

        response = self.testapp.get('/private-keys/new', status=403)
        self.assert_error_page(response)

    def test_create_requires_admin(self):
        self.be_normal_user()

        response = self.testapp.post(
            '/private-keys', params='key=key', status=403)
        self.assert_error_page(response)

    def test_admin_creates_key(self):
        self.be_admin_user()

        get_response = self.testapp.get('/private-keys/new')
        self.assertEqual(get_response.status_int, 200)
        form = get_response.form
        self.assertEqual(form.method, 'POST')

        form['key'] = 'key'
        post_response = form.submit()

        self.assertEqual(post_response.status_int, 302)
        self.assertEqual(post_response.headers['Location'],
                         'http://localhost:80/')
        self.assertEqual(PrivateKey.get(), 'key')
