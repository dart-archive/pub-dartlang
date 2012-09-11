# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from testcase import TestCase
import models

class ModelTest(TestCase):
    def testEllipsize(self):
        self.assertEquals("foo bar", models.ellipsize("foo bar", 7))
        self.assertEquals("foo...", models.ellipsize("foo bar baz", 7))
        self.assertEquals("foobarb...", models.ellipsize("foobarbaz", 7))
