# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import cherrypy
from google.appengine.ext.webapp.util import run_wsgi_app

from handlers.root import Root

run_wsgi_app(cherrypy.Application(Root()))
