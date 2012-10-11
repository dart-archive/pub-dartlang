# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from testcase import TestCase

class RootTest(TestCase):
    def test_admin_requires_login(self):
        response = self.testapp.get('/admin')
        self.assert_requires_login(response)

    def test_admin_requires_admin(self):
        self.be_normal_user()
        response = self.testapp.get('/admin', status=403)
        self.assert_error_page(response)
