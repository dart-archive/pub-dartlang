import cherrypy

import handlers

class Packages(handlers.Base):
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def create(self):
        return self.render("packages/create")
