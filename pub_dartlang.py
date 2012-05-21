import cherrypy
from google.appengine.ext.webapp.util import run_wsgi_app

import handlers

run_wsgi_app(cherrypy.Application(handlers.Root()))
