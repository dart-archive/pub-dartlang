# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

"""This module provides utility functions for models."""

from contextlib import contextmanager

from google.appengine.ext import db

@contextmanager
@db.transactional
def transaction():
    """Run a block of code in a transaction.

    Meant to be used with the 'with' keyword."""
    yield
