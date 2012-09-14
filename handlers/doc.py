# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import codecs
import os

import handlers

class Doc(object):
    """The handler for /doc/*."""

    def show(self, filename):
        if filename == '': filename = 'index.html'
        path = os.path.dirname(__file__) + '/../views/doc/' + filename
        if not os.path.isfile(path):
            handlers.http_error(404)
        with codecs.open(path, encoding='utf-8') as file:
            return handlers.layout(file.read())
