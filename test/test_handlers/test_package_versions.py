# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import yaml

from testcase import TestCase
from models.package import Package
from models.package_version import PackageVersion
from models.semantic_version import SemanticVersion

class PackageVersionsTest(TestCase):
    def setUp(self):
        super(PackageVersionsTest, self).setUp()
        self.package = Package.new(name='test-package', owner=self.admin_user())
        self.package.put()

    def test_new_requires_login(self):
        response = self.testapp.get('/packages/test-package/versions/new')
        self.assert_requires_login(response)

    def test_new_requires_ownership(self):
        self.be_normal_user()

        response = self.testapp.get('/packages/test-package/versions/new')
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost:80/packages/test-package')
        self.assertTrue(response.cookies_set.has_key('flash'))

    def test_owner_creates_package_version(self):
        self.be_admin_user()
        self.post_package_version('1.2.3')

        version = self.get_package_version('1.2.3')
        self.assertTrue(version is not None)
        self.assertEqual(version.version, SemanticVersion('1.2.3'))
        self.assertEqual(version.package.name, 'test-package')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3'))

    def test_create_requires_owner(self):
        self.be_normal_user()
        upload = self.upload_archive('test-package', '1.2.3')
        response = self.testapp.post(
            '/packages/test-package/versions', upload_files=[upload],
            status=403)
        self.assert_error_page(response)

    def test_create_requires_new_version_number(self):
        self.be_admin_user()
        self.package_version(self.package, '1.2.3', description='old').put()

        upload = self.upload_archive('test-package', '1.2.3', description='new')
        response = self.testapp.post('/packages/test-package/versions',
                                     upload_files=[upload])
        self.assertEqual(response.status_int, 302)
        self.assertEqual(
            response.headers['Location'],
            'http://localhost:80/packages/test-package/versions/new')
        self.assertTrue(response.cookies_set.has_key('flash'))

        version = self.get_package_version('1.2.3')
        self.assertEqual(version.pubspec['description'], 'old')

    def test_create_sets_latest_package_for_increased_version_number(self):
        self.be_admin_user()

        self.post_package_version('1.2.3')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3'))

        self.post_package_version('1.2.4')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.4'))

    def test_create_sets_latest_package_for_prerelease_versions_only(self):
        self.be_admin_user()

        self.post_package_version('1.2.3-pre1')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3-pre1'))

        self.post_package_version('1.2.3-pre0')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3-pre1'))

        self.post_package_version('1.2.3-pre2')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3-pre2'))

    def test_create_sets_latest_package_to_old_version_over_prerelease_version(self):
        self.be_admin_user()

        self.post_package_version('1.2.3-pre1')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3-pre1'))

        self.post_package_version('1.2.0')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.0'))

        self.post_package_version('1.2.3-pre2')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.0'))

    def test_create_doesnt_set_latest_package_for_decreased_version_number(self):
        self.be_admin_user()

        self.post_package_version('1.2.3')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3'))

        self.post_package_version('1.2.2')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3'))

    def test_create_doesnt_set_latest_package_for_prerelease_version_number(self):
        self.be_admin_user()

        self.post_package_version('1.2.3')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3'))

        self.post_package_version('1.2.5-pre')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3'))

    def test_create_sets_sort_order(self):
        self.be_admin_user()

        self.post_package_version('1.2.3')
        self.run_deferred_tasks()
        self.assertEqual(self.get_package_version('1.2.3').sort_order, 0)

        self.post_package_version('1.2.4')
        self.run_deferred_tasks()
        self.assertEqual(self.get_package_version('1.2.3').sort_order, 0)
        self.assertEqual(self.get_package_version('1.2.4').sort_order, 1)

        self.post_package_version('1.2.4-pre')
        self.run_deferred_tasks()
        self.assertEqual(self.get_package_version('1.2.3').sort_order, 0)
        self.assertEqual(self.get_package_version('1.2.4-pre').sort_order, 1)
        self.assertEqual(self.get_package_version('1.2.4').sort_order, 2)

    def test_show_package_version_tar_gz(self):
        version = self.package_version(self.package, '1.2.3')
        version.put()

        response = self.testapp.get(
            '/packages/test-package/versions/1.2.3.tar.gz')
        self.assertEqual(response.headers['Content-Type'],
                         'application/octet-stream')
        self.assertEqual(response.headers['Content-Disposition'],
                         'attachment; filename=test-package-1.2.3.tar.gz')
        self.assertEqual(response.body, self.tar_pubspec(version.pubspec))

    def test_show_package_version_yaml(self):
        version = self.package_version(self.package, '1.2.3',
            description="Test package!",
            dependencies={
                "test-dep1": "1.2.3",
                "test-dep2": {"git": "git://github.com/dart/test-dep2.git"}
            })
        version.put()

        response = self.testapp.get(
            '/packages/test-package/versions/1.2.3.yaml')
        self.assertEqual(response.headers['Content-Type'],
                         'text/yaml;charset=utf-8')
        self.assertEqual(yaml.load(response.body), version.pubspec)

    def post_package_version(self, version):
        get_response = self.testapp.get('/packages/test-package/versions/new')
        self.assertEqual(get_response.status_int, 200)
        form = get_response.form
        self.assertEqual(form.action, '/packages/test-package/versions')
        self.assertEqual(form.method, 'POST')

        contents = self.tar_pubspec(
            {'name': 'test-package', 'version': version})
        form['file'] = ('test-package-%s.tar.gz' % version, contents)
        post_response = form.submit()

        self.assertEqual(post_response.status_int, 302)
        self.assertEqual(
            post_response.headers['Location'],
            'http://localhost:80/packages/test-package')
        self.assertTrue(post_response.cookies_set.has_key('flash'))

    def latest_version(self):
        return Package.get_by_key_name('test-package').latest_version.version

    def get_package_version(self, version):
        return PackageVersion.get_by_name_and_version('test-package', version)
