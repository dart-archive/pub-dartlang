# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from cStringIO import StringIO

from testcase import TestCase
from models.package_version import PackageVersion

class PackageVersionTest(TestCase):
    def test_imports_from_archive(self):
        pubspec = {'name': 'test-package', 'version': '1.0.0'}
        archive = self.tar_package(pubspec, {
            'lib/foo.dart': '',
            'lib/bar/foo.dart': '',
            'lib/bar/src/foo.dart': '',
            'lib/zip': '',
            'lib/src/foo.dart': '',
        })
        version = PackageVersion.from_archive(StringIO(archive),
                                              uploader=self.admin_user())

        self.assertEqual(['bar/foo.dart', 'bar/src/foo.dart', 'foo.dart'],
                         version.libraries)

    def test_loads_readme_from_archive(self):
        pubspec = {'name': 'test-package', 'version': '1.0.0'}
        archive = self.tar_package(pubspec, {
            'README': 'This is a README.',
        })
        version = PackageVersion.from_archive(StringIO(archive),
                                              uploader=self.admin_user())
        self.assertEqual('This is a README.', version.readme.text)
