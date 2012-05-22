# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import cherrypy

import handlers
from handlers.packages import Packages

class Root(handlers.Base):
    @cherrypy.expose
    def index(self):
        return self.render('index')

    packages = Packages()
