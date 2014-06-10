# Copyright (c) 2013, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import json

from models.package import Package
from testcase import TestCase

class PackagesTest(TestCase):
    def test_api_index_lists_packages_in_update_order(self):
        self.be_admin_user()

        packages = ['armadillo', 'zebra', 'mongoose', 'snail']

        for package in packages:
            self.create_package(package, '1.0.0')

        # Make update time different than create time
        self.set_latest_version('mongoose', '1.0.1')

        self.be_normal_user()

        response = self.testapp.get('/api/packages')
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        result = json.loads(response.body)

        self.assertEqual(result['prev_url'], None)
        self.assertEqual(result['next_url'], None)
        self.assertEqual(result['pages'], 1)

        self.assertEqual(result['packages'][0]['name'], 'mongoose')
        self.assertEqual(result['packages'][0]['latest']['version'], '1.0.1')
        self.assertEqual(result['packages'][1]['name'], 'snail')
        self.assertEqual(result['packages'][2]['name'], 'zebra')
        self.assertEqual(result['packages'][3]['name'], 'armadillo')

    def test_api_index_lists_one_page_of_packages(self):
        self.be_admin_user()

        packages = ['package%d' % i for i in range(0, 200)]

        for package in packages:
            self.create_package(package, '1.0.0')

        self.be_normal_user()

        response = self.testapp.get('/api/packages')
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        result = json.loads(response.body)

        self.assertEqual(
            result['next_url'], 'http://localhost:80/api/packages?page=2')
        self.assertEqual(result['prev_url'], None)
        self.assertEqual(result['pages'], 2)

        for i in range(0, 100):
            self.assertEqual(result['packages'][i]['name'],
                             'package%d' % (199 - i))

    def test_api_index_lists_second_page_of_packages(self):
        self.be_admin_user()

        packages = ['package%d' % i for i in range(0, 200)]

        for package in packages:
            self.create_package(package, '1.0.0')

        self.be_normal_user()

        response = self.testapp.get('/api/packages?page=2')
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        result = json.loads(response.body)

        self.assertEqual(
            result['prev_url'], 'http://localhost:80/api/packages?page=1')
        self.assertEqual(result['next_url'], None)
        self.assertEqual(result['pages'], 2)

        for i in range(0, 100):
            self.assertEqual(result['packages'][i]['name'],
                             'package%d' % (99 - i))

    def test_api_get_non_existent_package(self):
        response = self.testapp.get(
            '/api/packages/test-package', status=404)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(json.loads(response.body), {
            'error': {'message': 'Package "test-package" doesn\'t exist.'}
        })

    def test_api_get_package_without_versions(self):
        admin = self.admin_user()
        Package.new(name='test-package', uploaders=[admin]).put()

        self.be_normal_user()

        response = self.testapp.get('/api/packages/test-package')
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        result = json.loads(response.body)
        self.assertEqual(result["name"], "test-package")
        self.assertEqual(result["versions"], [])
        self.assertEqual(result["latest"], None)

    def test_api_get_package_with_versions(self):
        self.be_admin_user()

        self.create_package('test-package', '1.1.0')
        self.create_package('test-package', '1.1.1')
        self.create_package('test-package', '1.2.0')

        self.be_normal_user()

        package = Package.get_by_key_name('test-package')

        response = self.testapp.get('/api/packages/test-package')
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(json.loads(response.body), {
            "name": "test-package",
            "url": "http://localhost:80/api/packages/test-package",
            "uploaders_url": "http://localhost:80/api/packages/test-package/" +
                "uploaders",
            "version_url": "http://localhost:80/api/packages/test-package/" +
                "versions/{version}",
            "new_version_url":
                "http://localhost:80/api/packages/test-package/versions/new",
            "downloads": 0,
            "uploaders": [self.admin_user().email()],
            "created": package.created.isoformat(),
            "versions": [
                self.package_version_dict("test-package", "1.1.0"),
                self.package_version_dict("test-package", "1.1.1"),
                self.package_version_dict("test-package", "1.2.0"),
            ],
            "latest": self.package_version_dict("test-package", "1.2.0")
        })

    # The following tests are to ensure that we invalidate the memcached
    # package data correctly.

    def test_api_get_package_sees_uploader_change(self):
        self._cache_test_package()

        # Add an uploader.
        response = self.testapp.post('/api/packages/test-package/uploaders',
                                     {'email': self.normal_user().email()})
        self.assertEqual(response.status_int, 200)

        # Request it again and make sure we get the updated list.
        response = self.testapp.get('/api/packages/test-package')
        self.assertEqual(json.loads(response.body)["uploaders"],
            [self.admin_user().email(), self.normal_user().email()])

        # Delete an uploader.
        response = self.testapp.delete(
            '/api/packages/test-package/uploaders/' +
                self.normal_user().email())
        self.assert_json_success(response)

        # Request it again and make sure we get the updated list.
        response = self.testapp.get('/api/packages/test-package')
        self.assertEqual(json.loads(response.body)["uploaders"],
            [self.admin_user().email()])

    def test_api_get_package_sees_upload(self):
        self._cache_test_package()

        # Upload a new version.
        self.post_package_version('1.2.3')

        # Request it again and make sure we get the updated list.
        response = self.testapp.get('/api/packages/test-package')
        self.assertEqual(json.loads(response.body)["versions"], [
            self.package_version_dict("test-package", "1.1.0"),
            self.package_version_dict("test-package", "1.1.1"),
            self.package_version_dict("test-package", "1.2.3")
        ])

    def _cache_test_package(self):
        """Create a test package and request its details so that the memcache
        is populated with it.

        This way, we can ensure that the cache is properly invalidated when a
        package changes."""
        self.be_admin_user()
        self.create_package('test-package', '1.1.0')
        self.create_package('test-package', '1.1.1')
        self.be_admin_oauth_user()

        # Request the package once to cache it.
        response = self.testapp.get('/api/packages/test-package')
        self.assertEqual(response.status_int, 200)
