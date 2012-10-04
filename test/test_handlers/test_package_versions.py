# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import re
import yaml

from google.appengine.api import users

from testcase import TestCase
from models.package import Package
from models.package_version import PackageVersion
from models.private_key import PrivateKey
from models.semantic_version import SemanticVersion

class PackageVersionsTest(TestCase):
    def setUp(self):
        super(PackageVersionsTest, self).setUp()
        self.package = Package.new(name='test-package', owner=self.admin_user())
        self.package.put()

    def test_admin_creates_new_package(self):
        self.be_admin_user()
        self.post_package_version(name='new-package', version='0.0.1')

        package = Package.get_by_key_name('new-package')
        self.assertTrue(package is not None)
        self.assertEqual(package.name, 'new-package')
        self.assertEqual(package.owner, users.get_current_user())

        version = package.version_set.get()
        self.assertTrue(version is not None)
        self.assertEqual(version.version, SemanticVersion('0.0.1'))
        self.assertEqual(version.package.name, 'new-package')

        version = package.latest_version
        self.assertTrue(version is not None)
        self.assertEqual(version.version, SemanticVersion('0.0.1'))
        self.assertEqual(version.package.name, 'new-package')

    def test_new_requires_login(self):
        response = self.testapp.get('/packages/test-package/versions/new')
        self.assert_requires_login(response)

    def test_new_requires_admin(self):
        self.be_normal_user()

        response = self.testapp.get('/packages/versions/new')
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost:80/packages')
        self.assertTrue(response.cookies_set.has_key('flash'))

    def test_new_requires_uploadership(self):
        self.be_normal_user()

        response = self.testapp.get('/packages/test-package/versions/new')
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost:80/packages/test-package')
        self.assertTrue(response.cookies_set.has_key('flash'))

    def test_new_requires_private_key(self):
        self.be_admin_user()
        PrivateKey.get_by_key_name('singleton').delete()

        response = self.testapp.get('/packages/test-package/versions/new')
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost:80/private-keys/new')

    def test_uploader_creates_package_version(self):
        self.be_admin_user()
        self.post_package_version('1.2.3')

        version = self.get_package_version('1.2.3')
        self.assertTrue(version is not None)
        self.assertEqual(version.version, SemanticVersion('1.2.3'))
        self.assertEqual(version.package.name, 'test-package')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3'))

    def test_create_requires_admin(self):
        self.be_normal_user()

        response = self.testapp.get('/packages/versions/abcd/create',
                                    status=403)
        self.assert_error_page(response)

    def test_create_requires_uploader(self):
        self.be_normal_user('owner')
        Package.new(name='owned-package').put()
        self.be_normal_user()

        response = self.testapp.get(
            '/packages/owned-package/versions/abcd/create', status=403)
        self.assert_error_page(response)

    def test_create_requires_valid_id(self):
        self.be_admin_user()

        response = self.testapp.get(
            '/packages/versions/abcd/create', status=403)
        self.assert_error_page(response)

    def test_create_requires_new_version_number(self):
        self.be_admin_user()
        self.package_version(self.package, '1.2.3', description='old').put()

        upload = self.upload_archive('test-package', '1.2.3', description='new')
        response = self.create_package(upload)
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
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost:80/gs_/packages/' +
                         'test-package-1.2.3.tar.gz')

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

    def post_package_version(self, version, name='test-package'):
        response = self.create_package(
            self.upload_archive(name, version))
        self.assertEqual(response.status_int, 302)
        self.assertEqual(
            response.headers['Location'],
            'http://localhost:80/packages/' + name)
        self.assertTrue(response.cookies_set.has_key('flash'))

    def create_package(self, upload, status=None):
        get_response = self.testapp.get('/packages/versions/new')
        self.assertEqual(get_response.status_int, 200)
        form = get_response.form
        self.assertEqual(form.method, 'POST')

        form['file'] = upload[1:]
        post_response = form.submit()

        self.assertEqual(post_response.status_int, 302)
        self.assertTrue(re.match(
                r'^http://localhost:80/packages/versions/[^/]+/create$',
                post_response.headers['Location']))

        path = post_response.headers['Location'].replace(
            'http://localhost:80', '')
        return self.testapp.get(path, status=status)

    def latest_version(self):
        return Package.get_by_key_name('test-package').latest_version.version

    def get_package_version(self, version):
        return PackageVersion.get_by_name_and_version('test-package', version)
