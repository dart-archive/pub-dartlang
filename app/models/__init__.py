# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

"""This module provides utility functions for models."""

from contextlib import contextmanager
import datetime
import re

import cherrypy
import routes

from decorator import decorator
from google.appengine.ext import db

@contextmanager
@db.transactional
def transaction():
    """Run a block of code in a transaction.

    Meant to be used with the 'with' keyword."""
    yield

@decorator
def transactional(fn, *args, **kwargs):
    """Like db.transactional, but preserves the original method signature.

    This is useful for wrapping handler actions, since CherryPy inspects the
    parameters to determine when to return a 404 response.
    """
    with transaction(): return fn(*args, **kwargs)

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

def validate_not_empty(list):
    """Validate that the value of a list property is not empty."""
    if len(list) == 0:
        raise db.BadValueError("List property must not be empty.")

def url(**kwargs):
    """Construct a URL for a given set of parametters.

    This must be run within a request context so that it can determine the base
    URL of the app.
    """
    return cherrypy.request.base + routes.url_for(**kwargs)

_HTTP_RE = re.compile(r"^https?://")

def nice_url(url):
    """Returns a human-readable version of URL.

    This removes the scheme. It returns None if the url is None."""
    if url is None: return None
    return _HTTP_RE.sub("", url)

def relative_date(date):
    """Construct a human-friendly relative date string like "2 hours ago".

    Arguments:
      date: The absolute date. The relative time will between this and the
            server's current time.
    """

    relative = datetime.datetime.utcnow() - date
    seconds = relative.seconds
    if relative.days > 7 or relative.days < 0:
        return date.strftime('%b %d, %Y')
    elif relative.days == 1:
        return '1 day ago'
    elif relative.days > 1:
        return '{} days ago'.format(relative.days)
    elif seconds <= 1:
        return 'just now'
    elif seconds < 60:
        return '{} seconds ago'.format(seconds)
    elif seconds < 120:
        return '1 minute ago'
    elif seconds < 3600:
        return '{} minutes ago'.format(seconds / 60)
    elif seconds < 7200:
        return '1 hour ago'
    else:
        return '{} hours ago'.format(seconds / 3600)
