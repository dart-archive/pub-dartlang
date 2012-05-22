import unittest

import cherrypy
import webtest
from google.appengine.ext.testbed import Testbed
from google.appengine.api import users

from handlers.root import Root

class TestCase(unittest.TestCase):
    def setUp(self):
        self.__users = {}
        self.__admins = {}

        self.testbed = Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_user_stub()

        self.testapp = webtest.TestApp(cherrypy.Application(Root()))

    def tearDown(self):
        self.testbed.deactivate()

    def normalUser(self, name = None):
        if self.__users.has_key(name):
            return self.__users[name]

        email = 'test-user@example.com'
        if name:
            email = 'test-user-%s@example.com' % name

        self.__users[name] = users.User(email = email)
        return self.__users[name]

    def adminUser(self, name = None):
        if self.__admins.has_key(name):
            return self.__admins[name]

        email = 'test-admin@example.com'
        if name:
            email = 'test-admin-%s@example.com' % name

        self.__admins[name] = users.User(email = email)
        return self.__admins[name]

    def beNormalUser(self, name = None):
        self.testbed.setup_env(
            user_email = self.normalUser(name).email(),
            overwrite = True)

    def beAdminUser(self, name = None):
        self.testbed.setup_env(
            user_email = self.adminUser(name).email(),
            user_is_admin = '1',
            overwrite = True)

    def assertErrorPage(self, response):
        # TODO(nweiz): Make a better error page that's easier to detect
        self.assertTrue(response.html.find('pre', id='traceback') is not None)
