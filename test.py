#!/usr/bin/env python
# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

"""The entrypoint for running tests.

If the App Engine dev_appserver.py is on $PATH, this can be run without any
arguments. Otherwise, it should be passed a single argument: the path to the App
Engine SDK.
"""

import optparse
import os
import sys
import subprocess

import unittest

USAGE = """%prog [SDK_PATH]
Run unit tests.

SDK_PATH    Path to the SDK installation.
            Auto-detected if dev_appserver.py is on $PATH."""

parser = optparse.OptionParser(USAGE)
parser.add_option('-n', '--name', help='the name of the test to run',
                  metavar='NAME')

options, args = parser.parse_args()
sdk_path = None
if len(args) > 1:
    print 'Error: 0 or 1 arguments required.'
    parser.print_help()
    sys.exit(1)
elif len(args) == 1:
    sdk_path = args[0]
else:
    process = subprocess.Popen(["which", "dev_appserver.py"],
                               stdout=subprocess.PIPE)
    stdout = process.communicate()[0]
    if process.returncode > 0:
        print('Error: could not find SDK path.')
        parser.print_help()
        sys.exit(1)
    sdk_path = os.path.dirname(stdout.strip())

sys.path.append(sdk_path)
import dev_appserver
dev_appserver.fix_sys_path()

import pub_dartlang

test_path = os.path.join(os.path.dirname(__file__), 'test')
loader = unittest.loader.TestLoader()
if options.name: loader.testMethodPrefix = options.name
unittest.TextTestRunner(verbosity = 2).run(loader.discover(test_path))
