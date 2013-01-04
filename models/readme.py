# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import cgi
import os
import re

import markdown

class Readme(object):
    """A README file with associated format information."""

    class Format(object):
        """An enum of possible README formats."""
        TEXT, MARKDOWN = range(2)

    def __init__(self, text, filename):
        self.text = text
        self.filename = filename

    @classmethod
    def from_archive(cls, tar):
        """Extract and return the README from a package archive.

        Return None if no README could be found.

        Arguments:
          tar: A TarFile object.
        """

        # If there are multiple READMEs, choose the one with the fewest
        # extensions. This handles the case where there are multiple READMEs in
        # different languages named e.g. "README.md" vs "README.jp.md".
        readmes = [name for name in tar.getnames()
                   if os.path.dirname(name) == ''
                   and re.match(r'^README($|\.)', name)]
        if len(readmes) == 0: return None

        filename = min(readmes, key=lambda(name): name.count('.'))
        text = unicode(tar.extractfile(filename).read(),
                       encoding='utf-8', errors='replace')
        return Readme(text, filename)

    @property
    def format(self):
        """Returns the format of the README as a value of Format."""
        return {
            ".md":       Readme.Format.MARKDOWN,
            ".markdown": Readme.Format.MARKDOWN,
            ".mdown":    Readme.Format.MARKDOWN,
        }.get(os.path.splitext(self.filename)[1], Readme.Format.TEXT)

    def render(self):
        """Renders the README to HTML."""
        return {
            Readme.Format.MARKDOWN: _render_markdown,
            Readme.Format.TEXT:     _render_text,
        }[self.format](self.text)

def _render_markdown(text):
    return markdown.markdown(
        text, output_format="html5", safe_mode='escape',
        extensions=['partial_gfm'])

def _render_text(text):
    return '<pre>%s</pre>' % cgi.escape(text)
