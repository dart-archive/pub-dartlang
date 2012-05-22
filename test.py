#!/usr/bin/python
import optparse
import os
import sys
import subprocess

import unittest2

USAGE = """%prog [SDK_PATH]
Run unit tests.

SDK_PATH    Path to the SDK installation.
            Auto-detected if dev_appserver.py is on $PATH."""


def main(sdk_path, test_path):
    sys.path.insert(0, sdk_path)
    import dev_appserver
    dev_appserver.fix_sys_path()
    suite = unittest2.loader.TestLoader().discover(test_path)
    unittest2.TextTestRunner(verbosity=2).run(suite)

parser = optparse.OptionParser(USAGE)
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

main(sdk_path, os.path.join(os.path.dirname(__file__), 'test'))
