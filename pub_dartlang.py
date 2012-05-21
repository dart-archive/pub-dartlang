import cherrypy

from google.appengine.ext.webapp.util import run_wsgi_app

class Root:
    @cherrypy.expose
    def index(self):
        return 'Hello World!'

run_wsgi_app(cherrypy.Application(Root()))
