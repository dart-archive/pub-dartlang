# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import unittest

import cherrypy
import webtest
from bs4 import BeautifulSoup
from google.appengine.ext.testbed import Testbed
from google.appengine.api import users

from handlers.root import Root

class TestCase(unittest.TestCase):
    """Utility methods for testing.

    This class should be used as the superclass of all other test classes. It
    sets up the necessary test stubs and provides various utility methods to use
    in tests.
    """

    def setUp(self):
        """Initialize stubs for testing.

        This initializes the following fields:
          self.testbed: An AppEngine Testbed used for mocking AppEngine
            services. This is activated, and any necessary stubs are
            initialized.
          self.testapp: A webtest.TestApp wrapping the CherryPy application.

        Subclasses that define their own setUp method should be sure to call
        this one as well.
        """

        self.__users = {}
        self.__admins = {}

        self.testbed = Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_user_stub()

        self.testapp = webtest.TestApp(cherrypy.Application(Root()))

    def tearDown(self):
        """Deactivates the stubs initialized in setUp.

        Subclasses that define their own tearDown method should be sure to call
        this one as well.
        """
        self.testbed.deactivate()

    def normalUser(self, name = None):
        """Constructs a non-admin user object.

        Arguments:
          name: A string to distinguish this user from others. Users with
            different names will be distinct, and the same name will always
            refer to the same user. Admin users have a separate namespace from
            non-admin users.

        Returns: The user object.
        """

        if self.__users.has_key(name):
            return self.__users[name]

        email = 'test-user@example.com'
        if name:
            email = 'test-user-%s@example.com' % name

        self.__users[name] = users.User(email = email)
        return self.__users[name]

    def adminUser(self, name = None):
        """Constructs an admin user object.

        Arguments:
          name: A string to distinguish this user from others. Users with
            different names will be distinct, and the same name will always
            refer to the same user. Admin users have a separate namespace from
            non-admin users.

        Returns: The user object.
        """

        if self.__admins.has_key(name):
            return self.__admins[name]

        email = 'test-admin@example.com'
        if name:
            email = 'test-admin-%s@example.com' % name

        self.__admins[name] = users.User(email = email)
        return self.__admins[name]

    def beNormalUser(self, name = None):
        """Log in as a non-admin user.

        Arguments:
          name: A string to distinguish this user from others. Users with
            different names will be distinct, and the same name will always
            refer to the same user. Admin users have a separate namespace from
            non-admin users.
        """
        self.testbed.setup_env(
            user_email = self.normalUser(name).email(),
            overwrite = True)

    def beAdminUser(self, name = None):
        """Log in as an admin user.

        Arguments:
          name: A string to distinguish this user from others. Users with
            different names will be distinct, and the same name will always
            refer to the same user. Admin users have a separate namespace from
            non-admin users.
        """
        self.testbed.setup_env(
            user_email = self.adminUser(name).email(),
            user_is_admin = '1',
            overwrite = True)

    def assertErrorPage(self, response):
        """Assert that the given response renders an HTTP error page.

        This only checks for HTTP errors; it will not detect flash error
        messages.

        Arguments:
          response: The webtest response object to check.
        """
        # TODO(nweiz): Make a better error page that's easier to detect
        error_pre = self.html(response).find('pre', id='traceback')
        self.assertTrue(error_pre is not None, "expected error page")

    def html(self, response):
        """Parse a webtest response with BeautifulSoup.

        WebTest includes built-in support for BeautifulSoup 3.x, but we want to
        be able to use the features in 4.x.

        Arguments:
          response: The webtest response object to parse.

        Returns: The BeautifulSoup parsed HTML.
        """
        return BeautifulSoup(response.body)
