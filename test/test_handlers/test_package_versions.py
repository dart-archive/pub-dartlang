# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import re
import json
import yaml

from google.appengine.api import users

import handlers
from testcase import TestCase
from models.package import Package
from models.package_version import PackageVersion
from models.private_key import PrivateKey
from models.semantic_version import SemanticVersion

class PackageVersionsTest(TestCase):
    def setUp(self):
        super(PackageVersionsTest, self).setUp()
        self.package = Package.new(
            name='test-package',
            uploaders=[self.admin_user(),
                       self.normal_user('other-uploader')])
        self.package.put()

    def test_user_creates_new_package(self):
        self.be_normal_oauth_user()
        self.post_package_version(name='new-package', version='0.0.1')

        package = Package.get_by_key_name('new-package')
        self.assertIsNotNone(package)
        self.assertEqual(package.name, 'new-package')
        self.assertEqual(package.uploaders, [handlers.get_current_user()])

        version = package.version_set.get()
        self.assertIsNotNone(version)
        self.assertEqual(version.version, SemanticVersion('0.0.1'))
        self.assertEqual(version.package.name, 'new-package')

        version = package.latest_version
        self.assertIsNotNone(version)
        self.assertEqual(version.version, SemanticVersion('0.0.1'))
        self.assertEqual(version.package.name, 'new-package')

        self.assertEqual(package.updated, version.created)
        self.assertEqual('This is a README.', version.readme.text)

    def test_show_package_version_tar_gz(self):
        version = self.package_version(self.package, '1.2.3')
        version.put()

        response = self.testapp.get(
            '/packages/test-package/versions/1.2.3.tar.gz')
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost:80/gs_/packages/' +
                         'test-package-1.2.3.tar.gz')

    def test_show_package_version_tar_gz_increments_downloads(self):
        self.be_admin_oauth_user()
        self.post_package_version('1.2.3')
        self.post_package_version('1.2.4')

        response = self.testapp.get(
            '/packages/test-package/versions/1.2.3.tar.gz')
        response = self.testapp.get(
            '/packages/test-package/versions/1.2.4.tar.gz')

        self.run_deferred_tasks()
        version = self.get_package_version('1.2.3')
        self.assertEqual(version.downloads, 1)
        self.assertEqual(version.package.downloads, 2)
        version = self.get_package_version('1.2.4')
        self.assertEqual(version.downloads, 1)
        self.assertEqual(version.package.downloads, 2)

        response = self.testapp.get(
            '/packages/test-package/versions/1.2.3.tar.gz')

        self.run_deferred_tasks()
        version = self.get_package_version('1.2.3')
        self.assertEqual(version.downloads, 2)
        self.assertEqual(version.package.downloads, 3)
        version = self.get_package_version('1.2.4')
        self.assertEqual(version.downloads, 1)
        self.assertEqual(version.package.downloads, 3)

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

    def test_uploader_gets_dartdoc_form(self):
        self.be_normal_oauth_user('other-uploader')
        self.post_package_version('1.2.3')

        response = self.testapp.get(
            '/packages/test-package/versions/1.2.3/new_dartdoc.json')
        content = json.loads(response.body)
        self.assertEqual(content['fields']['key'], 'pub.dartlang.org/ns' +
            '/staging/packages/test-package-1.2.3/dartdoc.json')
        self.assertEqual(content['fields']['acl'], 'public-read')

    def test_reload_requires_admin(self):
        self.be_normal_user()

        response = self.testapp.post('/packages/versions/reload', status=403)
        self.assert_error_page(response)

    def test_reload_reloads_a_package_version(self):
        self.be_admin_oauth_user()
        self.post_package_version('1.2.3')

        version = PackageVersion.get_by_name_and_version(
            'test-package', '1.2.3')
        version.libraries = ["wrong"]
        version.put()

        self.be_admin_user()
        response = self.testapp.post('/packages/versions/reload', status=302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost:80/admin#tab-packages')

        self.run_deferred_tasks()
        version = PackageVersion.get_by_name_and_version(
            'test-package', '1.2.3')
        self.assertEqual([], version.libraries)

        # The latest_version of the parent package should also be updated
        version = Package.get_by_key_name('test-package').latest_version
        self.assertEqual([], version.libraries)

        self.assert_package_updated_is_latest_version_created()

    def test_reload_preserves_sort_order(self):
        self.be_admin_oauth_user()
        self.post_package_version('1.2.3')
        self.post_package_version('1.2.4')
        self.post_package_version('1.2.4-pre')

        self.be_admin_user()
        self.testapp.post('/packages/versions/reload')
        self.run_deferred_tasks()

        version = PackageVersion.get_by_name_and_version(
            'test-package', '1.2.3')
        self.assertEqual(0, version.sort_order)

        version = PackageVersion.get_by_name_and_version(
            'test-package', '1.2.4-pre')
        self.assertEqual(1, version.sort_order)

        version = PackageVersion.get_by_name_and_version(
            'test-package', '1.2.4')
        self.assertEqual(2, version.sort_order)

    def test_reload_preserves_downloads(self):
        self.be_admin_oauth_user()
        self.post_package_version('1.2.3')

        response = self.testapp.get(
            '/packages/test-package/versions/1.2.3.tar.gz')

        self.be_admin_user()
        self.testapp.post('/packages/versions/reload')
        self.run_deferred_tasks()

        version = PackageVersion.get_by_name_and_version(
            'test-package', '1.2.3')
        self.assertEqual(1, version.downloads)

    def test_package_versions_are_indexed_by_canonical_version(self):
        self.be_admin_oauth_user()
        self.post_package_version('1.2.3')
        self.post_package_version('03.04.05')

        response = self.testapp.get(
            '/packages/test-package/versions/01.02.03.tar.gz')
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost:80/gs_/packages/' +
                         'test-package-1.2.3.tar.gz')

        response = self.testapp.get(
            '/packages/test-package/versions/3.4.5.tar.gz')
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.headers['Location'],
                         'http://localhost:80/gs_/packages/' +
                         'test-package-03.04.05.tar.gz')

    def post_package_version(self, version, name='test-package'):
        response = self.create_package(self.upload_archive(name, version))
        self.assert_json_success(response)

    def create_package(self, upload, status=None):
        get_response = self.testapp.get('/packages/versions/new.json')
        self.assertEqual(get_response.status_int, 200)
        content = json.loads(get_response.body)
        post_response = self.testapp.post(str(content['url']),
                                          content['fields'],
                                          upload_files=[upload])

        self.assertEqual(post_response.status_int, 302)
        self.assertTrue(re.match(
                r'^http://localhost:80/packages/versions/[^/]+/create\.json$',
                post_response.headers['Location']))

        path = post_response.headers['Location'].replace(
            'http://localhost:80', '')
        return self.testapp.get(path, status=status)

    def latest_version(self):
        return Package.get_by_key_name('test-package').latest_version.version

    def get_package_version(self, version):
        return PackageVersion.get_by_name_and_version('test-package', version)

    def assert_package_updated_is_latest_version_created(self):
        package = Package.get_by_key_name('test-package')
        self.assertEqual(package.updated, package.latest_version.created)
