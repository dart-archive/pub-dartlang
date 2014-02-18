# Copyright (c) 2014, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import cherrypy

import handlers

_REDIRECTS = {
  # /doc/ goes to "Getting started".
  '':                             'get-started.html',

  # Redirect from the old names for the commands.
  'pub-install.html':             'cmd/pub-get.html',
  'pub-update.html':              'cmd/pub-upgrade.html',

  # Most of the moved docs have the same name.
  'get-started.html':             'get-started.html',
  'dependencies.html':            'dependencies.html',
  'pubspec.html':                 'pubspec.html',
  'package-layout.html':          'package-layout.html',
  'assets-and-transformers.html': 'assets-and-transformers.html',
  'faq.html':                     'faq.html',
  'glossary.html':                'glossary.html',
  'versioning.html':              'versioning.html',

  # The command references were moved under "cmd".
  'pub-build.html':               'cmd/pub-build.html',
  'pub-cache.html':               'cmd/pub-cache.html',
  'pub-get.html':                 'cmd/pub-get.html',
  'pub-lish.html':                'cmd/pub-lish.html',
  'pub-upgrade.html':             'cmd/pub-upgrade.html',
  'pub-serve.html':               'cmd/pub-serve.html'
}

class Doc(object):
    """The handler for /doc/*."""

    def index(self):
        raise cherrypy.HTTPRedirect(
            'https://www.dartlang.org/tools/pub/get-started.html')

    def show(self, path):
        """Redirect to a documentation page on dartlang.org.

        Pub used to host its own docs, but no longer does. These redirects
        allow existing links to the docs to map to the new ones.
        """

        # Only redirect the known paths.
        try:
            redirect = _REDIRECTS[path]
            raise cherrypy.HTTPRedirect(
                'https://www.dartlang.org/tools/pub/' + redirect)
        except KeyError:
            handlers.http_error(404)
