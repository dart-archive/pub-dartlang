# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import tarfile

from google.appengine.ext import db
import yaml

class Pubspec(dict):
    """A parsed pubspec.yaml file."""

    @classmethod
    def from_archive(cls, file):
        """Extract and return the parsed pubspec from a package archive.

        After consuming the file, this puts the cursor back at the beginning.
        """
        try:
            tar = tarfile.open(mode="r:gz", fileobj=file)
            pubspec = yaml.load(tar.extractfile("pubspec.yaml").read())
            if not isinstance(pubspec, dict):
                raise db.BadValueError(
                    "Invalid pubspec, expected mapping at top level, was %s" %
                    pubspec)
            file.seek(0)
            return cls(pubspec)
        except (tarfile.TarError, KeyError) as err:
            raise db.BadValueError(
                "Error parsing package archive: %s" % err)
        except yaml.YAMLError as err:
            raise db.BadValueError("Error parsing pubspec: %s" % err)

    def required(self, key):
        """Return a value from the pubspec, and assert that it exists."""
        if key not in self:
            raise db.BadValueError("Pubspec is missing required key '%s'" % key)
        return self[key]
