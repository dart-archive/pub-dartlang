import cherrypy
from google.appengine.ext.webapp.util import run_wsgi_app

from handlers.root import Root

run_wsgi_app(cherrypy.Application(Root()))
