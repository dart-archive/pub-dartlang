# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from testcase import TestCase

class VersionNegotiationTest(TestCase):
    # TODO(nweiz): when we have any actions that change behavior based on the
    # API version, test that. Also test that the latest version is the default.

    def test_rejects_too_low_version(self):
        self.testapp.get(
            '/api/packages',
            headers={'Accept': 'application/vnd.pub.v1+json'},
            status=406)

    def test_rejects_too_high_version(self):
        self.testapp.get(
            '/api/packages',
            headers={'Accept': 'application/vnd.pub.v3+json'},
            status=406)

    def test_rejects_malformed_version(self):
        self.testapp.get(
            '/api/packages',
            headers={'Accept': 'application/vnd.pub.asdf+json'},
            status=406)

    def test_rejects_malformed_format(self):
        self.testapp.get(
            '/api/packages',
            headers={'Accept': 'application/vnd.pub.v2+yaml'},
            status=406)
