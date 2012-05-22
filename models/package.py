# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from google.appengine.ext import db

class Package(db.Model):
    owner = db.UserProperty(auto_current_user_add = True)
    name = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add = True)
    updated = db.DateTimeProperty(auto_now = True)

    def __init__(self, *args, **kwargs):
        kwargs['key_name'] = kwargs['name']
        super(Package, self).__init__(*args, **kwargs)

    @classmethod
    def exists(cls, name):
        return cls.get_by_key_name(name) is not None

    @classmethod
    @db.transactional
    def create_unless_exists(cls, name):
        if cls.exists(name):
            return False

        cls(name = name).put()
        return True
