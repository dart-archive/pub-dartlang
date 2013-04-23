# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from testcase import TestCase

from models.package import Package

class ErrorTest(TestCase):
    def test_error_traceback_requires_admin(self):
        self.set_is_dev_server(False)

        self.be_normal_user()
        response = self.testapp.get('/not/real/here/comes/a/404', status=404)
        self.assert_error_page(response)
        self.assertIsNone(self.html(response).find('pre', 'traceback'))

        self.be_admin_user()
        response = self.testapp.get('/not/real/here/comes/a/404', status=404)
        self.assert_error_page(response)
        self.assertIsNotNone(self.html(response).find('pre', 'traceback'))

        self.set_is_dev_server(None)
