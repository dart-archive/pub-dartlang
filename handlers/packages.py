import cherrypy
from google.appengine.api import users

import handlers

class Packages(handlers.Base):
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def create(self):
        if not users.get_current_user():
            raise cherrypy.HTTPRedirect(
                users.create_login_url(cherrypy.url()))
        elif not users.is_current_user_admin():
            self.flash('Currently only admins may create packages.')
            raise cherrypy.HTTPRedirect('/packages')

        return self.render("packages/create")
