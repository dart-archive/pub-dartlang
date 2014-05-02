# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from testcase import TestCase

from models.private_key import PrivateKey

class PrivateKeysTest(TestCase):
    def test_create_requires_admin(self):
        self.be_normal_user()

        response = self.testapp.post(
            '/private-keys', params='oauth_key=oauth&api_key=api', status=403)
        self.assert_error_page(response)

    def test_admin_creates_keys(self):
        self.be_admin_user()

        get_response = self.testapp.get('/admin')
        self.assertEqual(get_response.status_int, 200)
        form = get_response.forms["private-key"]
        self.assertEqual(form.method, 'POST')

        form['oauth_key'] = 'oauth'
        form['api_key'] = 'api'
        post_response = form.submit()

        self.assertEqual(post_response.status_int, 302)
        self.assertEqual(post_response.headers['Location'],
                         'http://localhost:80/admin#tab-private-keys')
        self.assertEqual(PrivateKey.get_oauth(), 'oauth')
        self.assertEqual(PrivateKey.get_api(), 'api')
