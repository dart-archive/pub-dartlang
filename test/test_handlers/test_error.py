# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from testcase import TestCase, mock_not_on_dev_server

from models.package import Package

class ErrorTest(TestCase):
    def test_error_traceback_shown_on_dev_server(self):
        self.be_normal_user()
        response = self.testapp.get('/not/real/here/comes/a/404', status=404)
        self.assert_error_page(response)
        self.assertIsNotNone(self.html(response).find('pre', 'traceback'))

    @mock_not_on_dev_server
    def test_error_traceback_shown_to_admin(self):
        self.be_admin_user()
        response = self.testapp.get('/not/real/here/comes/a/404', status=404)
        self.assert_error_page(response)
        self.assertIsNotNone(self.html(response).find('pre', 'traceback'))

    @mock_not_on_dev_server
    def test_error_traceback_not_shown(self):
        self.be_normal_user()
        response = self.testapp.get('/not/real/here/comes/a/404', status=404)
        self.assert_error_page(response)
        self.assertIsNone(self.html(response).find('pre', 'traceback'))
