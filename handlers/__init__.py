import os

import cherrypy
from google.appengine.api import users

import pystache

renderer = pystache.Renderer(search_dirs = [
        os.path.join(os.path.dirname(__file__), '../views')])

class Base:
    def render(self, name, *context, **kwargs):
        content = renderer.render(
            renderer.load_template(name), *context, **kwargs)

        return renderer.render(
            renderer.load_template("layout"),
            content = content,
            logged_in = users.get_current_user() is not None,
            login_url = users.create_login_url(cherrypy.url()),
            logout_url = users.create_logout_url(cherrypy.url()))
