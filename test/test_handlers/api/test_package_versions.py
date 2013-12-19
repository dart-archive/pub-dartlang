# Copyright (c) 2013, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import re
import json

import handlers
from models.package import Package
from models.package_version import PackageVersion
from models.private_key import PrivateKey
from models.semantic_version import SemanticVersion
from testcase import TestCase

class PackageVersionsTest(TestCase):
    def setUp(self):
        super(PackageVersionsTest, self).setUp()
        self.package = Package.new(
            name='test-package',
            uploaders=[self.admin_user(),
                       self.normal_user('other-uploader')])
        self.package.put()

    def test_api_user_creates_new_package(self):
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

    def test_api_uploadership_is_case_insensitive(self):
        self.be_normal_oauth_user('NAme')
        self.post_package_version(name='new-package', version='0.0.1')

        version = Package.get_by_key_name('new-package').latest_version
        self.assertIsNotNone(version)
        self.assertEqual(version.version, SemanticVersion('0.0.1'))

        self.be_normal_oauth_user('naME')
        self.post_package_version(name='new-package', version='0.0.2')

        version = Package.get_by_key_name('new-package').latest_version
        self.assertIsNotNone(version)
        self.assertEqual(version.version, SemanticVersion('0.0.2'))

    def test_api_new_requires_oauth(self):
        response = self.testapp.get('/api/packages/versions/new',
                                    status=401)
        self.assert_json_error(response)
        # Since we didn't send any OAuth2 credentials, the WWW-Authenticate
        # header shouldn't have OAuth2-specific fields.
        self.assertEqual(response.headers['WWW-Authenticate'], 'Bearer')

    def test_api_new_requires_private_key(self):
        self.be_admin_oauth_user()
        PrivateKey.get_by_key_name('singleton').delete()

        response = self.testapp.get('/api/packages/versions/new',
                                    status=500)
        self.assert_json_error(response)

    def test_api_uploader_creates_package_version(self):
        self.be_normal_oauth_user('other-uploader')
        self.post_package_version('1.2.3')

        version = self.get_package_version('1.2.3')
        self.assertIsNotNone(version)
        self.assertEqual(version.version, SemanticVersion('1.2.3'))
        self.assertEqual(version.package.name, 'test-package')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3'))

    def test_api_create_requires_admin(self):
        self.be_normal_oauth_user()

        response = self.testapp.get('/api/packages/versions/abcd/create',
                                    status=403)
        self.assert_json_error(response)

    def test_api_create_requires_uploader(self):
        Package.new(name='owned-package',
                    uploaders=[self.normal_user('owner')]).put()
        self.be_normal_oauth_user()

        response = self.testapp.get(
            '/api/packages/owned-package/versions/abcd/create', status=403)
        self.assert_json_error(response)

    def test_api_create_requires_valid_id(self):
        self.be_admin_oauth_user()

        response = self.testapp.get(
            '/packages/versions/abcd/create.json', status=403)
        self.assert_json_error(response)

    def test_api_create_requires_new_version_number(self):
        self.be_admin_oauth_user()
        self.package_version(self.package, '1.2.3', description='old').put()

        upload = self.upload_archive('test-package', '1.2.3', description='new')
        response = self.create_package(upload, status=400)
        self.assert_json_error(response)

        version = self.get_package_version('1.2.3')
        self.assertEqual(version.pubspec['description'], 'old')

    def test_api_create_sets_latest_package_for_increased_version_number(self):
        self.be_admin_oauth_user()

        self.post_package_version('1.2.3')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3'))

        self.post_package_version('1.2.4')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.4'))

        self.assert_package_updated_is_latest_version_created()

    def test_api_create_sets_latest_package_for_prerelease_versions_only(self):
        self.be_admin_oauth_user()

        self.post_package_version('1.2.3-pre1')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3-pre1'))

        self.post_package_version('1.2.3-pre0')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3-pre1'))

        self.post_package_version('1.2.3-pre2')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3-pre2'))

        self.assert_package_updated_is_latest_version_created()

    def test_api_create_sets_latest_package_to_old_version_over_prerelease_version(self):
        self.be_admin_oauth_user()

        self.post_package_version('1.2.3-pre1')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3-pre1'))

        self.post_package_version('1.2.0')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.0'))

        self.post_package_version('1.2.3-pre2')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.0'))

        self.assert_package_updated_is_latest_version_created()

    def test_api_create_doesnt_set_latest_package_for_decreased_version_number(self):
        self.be_admin_oauth_user()

        self.post_package_version('1.2.3')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3'))

        self.post_package_version('1.2.2')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3'))

        self.assert_package_updated_is_latest_version_created()

    def test_api_create_doesnt_set_latest_package_for_prerelease_version_number(self):
        self.be_admin_oauth_user()

        self.post_package_version('1.2.3')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3'))

        self.post_package_version('1.2.5-pre')
        self.assertEqual(self.latest_version(), SemanticVersion('1.2.3'))

        self.assert_package_updated_is_latest_version_created()

    def test_api_create_sets_sort_order(self):
        self.be_admin_oauth_user()

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

    def test_api_show_package_version(self):
        version = self.package_version(self.package, '1.2.3')
        version.put()

        response = self.testapp.get('/api/packages/test-package/versions/1.2.3')
        self.assertEqual(response.headers['Content-Type'], 'application/json')

        self.maxDiff = None
        expected = self.package_version_dict('test-package', '1.2.3')
        expected.update({
            'created': version.created.isoformat(),
            'downloads': 0,
            'libraries': [],
            'uploader': self.admin_user().email()
        })
        self.assertEqual(json.loads(response.body), expected)

    def test_api_dartdoc_requires_private_key(self):
        self.be_admin_oauth_user()
        self.post_package_version('1.2.3')
        PrivateKey.get_by_key_name('singleton').delete()

        response = self.testapp.get(
            '/api/packages/test-package/versions/1.2.3/new_dartdoc',
            status=500)
        self.assert_json_error(response)

    def test_api_dartdoc_requires_uploadership(self):
        self.be_admin_oauth_user()
        self.post_package_version('1.2.3')

        self.be_normal_oauth_user()
        response = self.testapp.get(
            '/api/packages/test-package/versions/1.2.3/new_dartdoc',
            status=403)
        self.assert_json_error(response)

    def test_api_uploader_gets_dartdoc_form(self):
        self.be_normal_oauth_user('other-uploader')
        self.post_package_version('1.2.3')

        response = self.testapp.get(
            '/api/packages/test-package/versions/1.2.3/new_dartdoc')
        content = json.loads(response.body)
        self.assertEqual(content['fields']['key'], 'pub.dartlang.org/ns' +
            '/staging/packages/test-package-1.2.3/dartdoc.json')
        self.assertEqual(content['fields']['acl'], 'public-read')

    def test_api_uploader_gets_dartdoc_form_for_nonexistent_package(self):
        self.be_normal_oauth_user('other-uploader')

        response = self.testapp.get(
            '/packages/not-package/versions/1.2.3/new_dartdoc.json',
            status=404)
        self.assert_json_error(response)

    def test_api_malformed_package_version(self):
        version = self.package_version(self.package, '1.2.3')
        version.put()

        response = self.testapp.get(
            '/api/packages/test-package/versions/banana', status=400)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(json.loads(response.body), {
            'error': {'message': '"banana" is not a valid semantic version.'}
        })

    def test_api_no_such_package_version(self):
        version = self.package_version(self.package, '1.2.3')
        version.put()

        response = self.testapp.get(
            '/api/packages/test-package/versions/2.0.0', status=404)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(json.loads(response.body), {
            'error':
            {'message': '"test-package" version 2.0.0 doesn\'t exist.'}
        })

    def post_package_version(self, version, name='test-package'):
        response = self.create_package(self.upload_archive(name, version))
        self.assert_json_success(response)

    def create_package(self, upload, status=None):
        get_response = self.testapp.get('/api/packages/versions/new')
        self.assertEqual(get_response.status_int, 200)
        content = json.loads(get_response.body)
        post_response = self.testapp.post(str(content['url']),
                                          content['fields'],
                                          upload_files=[upload])

        self.assertEqual(post_response.status_int, 302)
        self.assertTrue(re.match(
                r'^http://localhost:80/api/packages/versions/[^/]+/create$',
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
