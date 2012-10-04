# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import codecs
import itertools
import os
import re

import yaml

import handlers

class Doc(object):
    """The handler for /doc/*."""

    def show(self, filename):
        """Display a documentation page.

        Each page is static HTML wrapped in a dynamic layout. The HTML is
        generated offline from Markdown source files in /doc; the titles are
        loaded from those source files as well.
        """

        if filename == '': filename = 'index.html'
        root = os.path.join(os.path.dirname(__file__), '..')

        html_path = os.path.join(root, 'views', 'doc', filename)
        if not os.path.isfile(html_path):
            handlers.http_error(404)

        markdown_filename = re.sub("\.html$", ".markdown", filename)
        markdown_path = os.path.join(root, 'doc', markdown_filename)
        with codecs.open(markdown_path, encoding='utf-8') as f:
            frontmatter = self._frontmatter(f)

        with codecs.open(html_path, encoding='utf-8') as f:
            html = """<article>
                <h1>%s</h1>
                %s
                </article>""" % (frontmatter['title'], f.read())
            return handlers.layout(html)

    def _frontmatter(self, f):
        """Parses the YAML frontmatter of a file."""
        if f.readline() != '---\n': return {}
        yaml_lines = itertools.takewhile(lambda line: line != '---\n', f)
        return yaml.load(''.join(yaml_lines))
