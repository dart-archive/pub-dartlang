# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

def is_str(value):
    """Return whether or not value is a string (either str or unicode)."""
    return isinstance(value, str) or isinstance(value, unicode)
