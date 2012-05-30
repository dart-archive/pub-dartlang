# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import handlers

class Root(object):
    """The handler for /*."""

    def index(self):
        """Retrieves the front page of the package server."""
        return handlers.render('index')
