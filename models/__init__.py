# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

"""This module provides utility functions for models."""

from contextlib import contextmanager
import re

from google.appengine.ext import db

@contextmanager
@db.transactional
def transaction():
    """Run a block of code in a transaction.

    Meant to be used with the 'with' keyword."""
    yield

_ELLIPSIZE_RE = re.compile(r"(\s+[^\s]*)?$")

def ellipsize(string, max):
    """Truncate a string and adds an ellipsis at the end.

    This function ensures that the ellipsis appears between words if possible.

    Arguments:
      string: The string to truncate.
      max: The maximum length of the string, over which it will be truncated.

    Returns: The truncated string.
    """

    if len(string) <= max: return string
    return _ELLIPSIZE_RE.sub("...", string[0:max])
