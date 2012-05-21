import os

import cherrypy
import pystache

renderer = pystache.Renderer(search_dirs = [
        os.path.join(os.path.dirname(__file__), '../views')])

class Base:
    def render(self, name, *context, **kwargs):
        content = renderer.render(
            renderer.load_template(name), *context, **kwargs)
        return renderer.render(renderer.load_template("layout"),
                               content = content)

class Root(Base):
    @cherrypy.expose
    def index(self):
        return self.render('index')
