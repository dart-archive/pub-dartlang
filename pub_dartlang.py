import cherrypy

from google.appengine.ext.webapp.util import run_wsgi_app

class Root:
    @cherrypy.expose
    def index(self):
        return 'Hello World!'

application = cherrypy.Application(Root())

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
