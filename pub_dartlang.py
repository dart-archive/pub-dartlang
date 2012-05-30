# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

"""The entrypoint for the pub.dartlang.org server.

In development, this should be run using the App Engine dev_appserver.py script.
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'third_party'))

import cherrypy
from google.appengine.ext.webapp.util import run_wsgi_app

from handlers.root import Root

class Application(cherrypy.Application):
    """The pub.dartlang.org WSGI application."""

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(Root(), *args, **kwargs)

if __name__ == "__main__":
    run_wsgi_app(Application())
