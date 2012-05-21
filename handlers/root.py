import cherrypy

import handlers
from handlers.packages import Packages

class Root(handlers.Base):
    @cherrypy.expose
    def index(self):
        return self.render('index')

    packages = Packages()
