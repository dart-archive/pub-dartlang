# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import os
import re

class Readme(object):
    """A README file with associated format information."""

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

        readmes = [name for name in tar.getnames()
                   if os.path.dirname(name) == ''
                   and re.match(r'^README($|\.)', name)]
        if len(readmes) == 0: return None

        filename = min(readmes, key=lambda(name): name.count('.'))
        text = tar.extractfile(filename).read()
        return Readme(text, filename)
