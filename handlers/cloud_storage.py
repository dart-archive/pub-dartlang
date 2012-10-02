# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

"""Utility functions for dealing with Google Cloud Storage."""

from base64 import b64encode
from urlparse import urlparse, parse_qs
import handlers
import json
import urllib
import time

from google.appengine.api import app_identity
from google.appengine.api import files
from google.appengine.api import urlfetch

from models.private_key import PrivateKey

# The Google Cloud Storage bucket for this app
_BUCKET = "pub.dartlang.org"

# From https://code.google.com/apis/console
_ACCESS_KEY = "818368855108@developer.gserviceaccount.com"

# From https://developers.google.com/storage/docs/authentication
_FULL_CONTROL_SCOPE = "https://www.googleapis.com/auth/devstorage.full_control"

def upload_form(obj, lifetime=10*60, acl=None, cache_control=None,
                content_disposition=None, content_encoding=None,
                content_type=None, expires=None, success_redirect=None,
                success_status=None, size_range=None, metadata={}):
    """Returns the HTML for a form that will upload a file to cloud storage.

    Most arguments are identical to the form fields listed in
    https://developers.google.com/storage/docs/reference-methods#postobject, but
    there are a few differences:

    * The expires argument takes a number of seconds since the epoch.
    * The key argument only specifies the key name, not the bucket.
    * The metadata argument is a dictionary of metadata header names to values.
      Each one is transformed into an x-goog-meta- field. The keys should not
      include "x-goog-meta-". Null values are ignored.
    * The policy document is automatically created and signed. It ensures that
      all fields have the assigned values when they're submitted to Cloud
      Storage.

    The lifetime argument specifies how long the form is valid. It defaults to
    ten minutes.

    The size_range argument should be a tuple indicating the lower and upper
    bounds on the size of the uploaded file, in bytes.
    """

    obj = _BUCKET + '/' + obj

    metadata = {'x-goog-meta-' + key: value for key, value
                in metadata.iteritems()}
    if expires is not None: expires = _iso8601(expires)

    policy = {}
    policy['expiration'] = _iso8601(time.time() + lifetime)
    policy['conditions'] = [{'key': obj}]
    def _try_add_condition(name, value):
        if value is not None: policy['conditions'].append({name: value})
    _try_add_condition('acl', acl)
    _try_add_condition('cache-control', cache_control)
    _try_add_condition('content-disposition', content_disposition)
    _try_add_condition('content-encoding', content_encoding)
    _try_add_condition('content-type', content_type)
    _try_add_condition('expires', expires)
    _try_add_condition('success_action_redirect', success_redirect)
    _try_add_condition('success_action_status', success_status)
    for key, value in metadata.items(): _try_add_condition(key, value)
    if size_range is not None:
        policy['conditions'].append(
            ['content-length-range', size_range[0], size_range[1]])
    policy = b64encode(json.dumps(policy))
    signature = PrivateKey.sign(policy)

    fields = {'key': obj, 'acl': acl,
              'Cache-Control': cache_control,
              'Content-Disposition': content_disposition,
              'Content-Encoding': content_encoding,
              'Content-Type': content_type, 'expires': expires,
              'GoogleAccessId': _ACCESS_KEY, 'policy': policy,
              'signature': signature,
              'success_action_redirect': success_redirect,
              'success_action_status': success_status}
    fields.update(metadata)
    # Get the fields into a format mustache can iterate over
    fields = [{'key': key, 'value': value} for key, value in fields.iteritems()]

    url = ("https://storage.googleapis.com" if handlers.production()
           else handlers.request().url(controller="versions", action="upload"))
    return handlers.render("signed_form", url=url, fields=fields, layout=False)

def modify_object(obj, content_encoding=None, content_type=None,
                  content_disposition=None, acl=None, copy_source=None,
                  copy_source_if_match=None, copy_source_if_none_match=None,
                  copy_source_if_modified_since=None,
                  copy_source_if_unmodified_since=None,
                  copy_metadata=True, metadata={}):
    """Modifies or copies a cloud storage object.

    Most arguments are identical to the form fields listed in
    https://developers.google.com/storage/docs/reference-methods#putobject, but
    there are a few differences:

    * The copy_metadata argument can be True, indicating that the metadata
      should be copied, or False, indicating that it should be replaced.
    * The metadata argument is a dictionary of metadata header names to values.
      Each one is transformed into an x-goog-meta- field. The keys should not
      include "x-goog-meta-". Null values are ignored.
    """

    obj = _BUCKET + "/" + obj
    if copy_source is not None: copy_source = _BUCKET + "/" + copy_source

    if not handlers.production():
        # The only way to modify an existing object using only the Python API
        # seems to be to copy it over itself. It's not a big deal since this is
        # only for development.
        if copy_source is None: copy_source = obj
        contents = None
        with files.open('/gs/' + copy_source, 'r') as f: contents = f.read()

        if content_type is None: content_type = 'application/octet-stream'
        write_path = files.gs.create('/gs/' + obj, mime_type=content_type,
                                     acl=acl, content_encoding=content_encoding,
                                     content_disposition=content_disposition,
                                     user_metadata=metadata)
        with files.open(write_path, 'a') as f: f.write(contents)
        files.finalize(write_path)
        return

    auth = "OAuth " + app_identity.get_access_token(_FULL_CONTROL_SCOPE)[0]
    headers = {
        "Authorization": auth,
        "Content-Encoding": content_encoding,
        "Content-Type": content_type,
        "Content-Disposition": content_disposition,
        "x-goog-api-version": "2",
        "x-goog-acl": acl,
        "x-goog-copy-source": copy_source,
        "x-goog-copy-source-if-match": copy_source_if_match,
        "x-goog-copy-source-if-none-match": copy_source_if_none_match,
        "x-goog-copy-source-if-modified-since": copy_source_if_modified_since,
        "x-goog-copy-source-if-unmodified-since":
            copy_source_if_unmodified_since,
        "x-goog-copy-metadata-directive":
            "COPY" if copy_metadata else "REPLACE"
    }
    for (key, value) in metadata.iteritems():
        headers["x-goog-meta-" + key] = value
    headers = {key: value for key, value in headers.iteritems()
               if value is not None}

    return urlfetch.fetch("https://storage.googleapis.com/" + urllib.quote(obj),
                          method="PUT", headers=headers)

def delete_object(obj):
    """Deletes an object from cloud storage."""
    files.delete('/gs/' + _BUCKET + '/' + obj)

def open(obj):
    """Opens an object in cloud storage."""
    return files.open('/gs/' + _BUCKET + '/' + obj, 'r')

def _iso8601(secs):
    """Returns the ISO8601 representation of the given time.

    The time should be in seconds past the epoch."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(secs))
