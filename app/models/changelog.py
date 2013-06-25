# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import cgi
import os
import re

import markdown

class Changelog(object):
    """A CHANGELOG file with associated format information."""

    class Format(object):
        """An enum of possible CHANGELOG formats."""
        TEXT, MARKDOWN = range(2)

    def __init__(self, text, filename):
        self.text = text
        self.filename = filename

    @classmethod
    def from_archive(cls, tar):
        """Extract and return the CHANGELOG from a package archive.

        Return None if no CHANGELOG could be found.

        Arguments:
          tar: A TarFile object.
        """

        # If there are multiple CHANGELOGs, choose the one with the fewest
        # extensions. This handles the case where there are multiple CHANGELOGs
        # in different languages named e.g. "CHANGELOG.md" vs "CHANGELOG.jp.md".
        changelogs = [name for name in tar.getnames()
                      if os.path.dirname(name) == ''
                      and re.match(r'^CHANGELOG($|\.)', name, re.IGNORECASE)]
        if len(changelogs) == 0: return None

        filename = min(changelogs, key=lambda(name): (name.count('.'), name))
        text = unicode(tar.extractfile(filename).read(),
                       encoding='utf-8', errors='replace')
        return Changelog(text, filename)

    @property
    def format(self):
        """Returns the format of the CHANGELOG as a value of Format."""
        return {
            ".md":       Changelog.Format.MARKDOWN,
            ".markdown": Changelog.Format.MARKDOWN,
            ".mdown":    Changelog.Format.MARKDOWN,
        }.get(os.path.splitext(self.filename)[1].lower(), Changelog.Format.TEXT)

    def render(self):
        """Renders the CHANGELOG to HTML."""
        return {
            Changelog.Format.MARKDOWN: _render_markdown,
            Changelog.Format.TEXT:     _render_text,
        }[self.format](self.text)

def _render_markdown(text):
    return markdown.markdown(
        text, output_format="html5", safe_mode='escape',
        extensions=['partial_gfm'])

def _render_text(text):
    return '<pre>%s</pre>' % cgi.escape(text)
