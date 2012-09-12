# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from google.appengine.ext import db
import json

from pubspec import Pubspec
from semantic_version import SemanticVersion

class DocumentProperty(db.Property):
    """A property that stores a JSON-encodable document."""

    data_type = dict

    def get_value_for_datastore(self, model_instance):
        """Dump the document to JSON."""
        value = super(DocumentProperty, self) \
            .get_value_for_datastore(model_instance)
        return json.dumps(value)

    def make_value_from_datastore(self, value):
        """Load the document from JSON."""
        if value is None:
            return None
        return json.loads(value)

class PubspecProperty(DocumentProperty):
    """A property that stores a parsed Pubspec."""

    data_type = Pubspec

    def make_value_from_datastore(self, value):
        """Load the pubspec from JSON."""
        contents = super(PubspecProperty, self).make_value_from_datastore(value)
        return Pubspec(contents)

class VersionProperty(db.Property):
    """A property that stores a semantic version."""

    data_type = SemanticVersion

    def get_value_for_datastore(self, model_instance):
        value = super(VersionProperty, self) \
            .get_value_for_datastore(model_instance)
        return str(value)

    def make_value_from_datastore(self, value):
        if value is None:
            return None
        return SemanticVersion(value)
