# Copyright (c) 2014, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from google.appengine.api import users

from testcase import TestCase

import handlers.search as search
from models.package_version import PackageVersion
from models.private_key import PrivateKey
from models.pubspec import Pubspec

class SearchTest(TestCase):
    def setUp(self):
        super(SearchTest, self).setUp()

        self.be_admin_user()
        packages = [
            "armadillo", "bandicoot", "cat", "dog", "elephant",
            "fox", "gorilla", "hippo", "iguana", "jackal",
            "kangaroo", "lemur"
        ]

        for package in packages:
            self.create_package(package, "1.0.0")
            packageVersion = PackageVersion.get_by_name_and_version(
                package, "1.0.0")
            packageVersion.pubspec.update(
                description="Description for " + package)
            packageVersion.put()

        self.be_normal_user()

    def test_index_show_results(self):
        self.mock_results(["armadillo", "bandicoot", "cat", "dog", "elephant"])

        self.assert_list_in_html("/search?q=query", "tbody tr", [
            "armadillo", "bandicoot", "cat", "dog", "elephant"
        ])

    def test_index_paginates_results(self):
        self.mock_results([
            "armadillo", "bandicoot", "cat", "dog", "elephant",
            "fox", "gorilla", "hippo", "iguana", "jackal"
        ], 12)

        self.assert_list_in_html("/search?q=query", "tbody tr", [
            "armadillo", "bandicoot", "cat", "dog", "elephant",
            "fox", "gorilla", "hippo", "iguana", "jackal"
        ])

        self.mock_results([
            "kangaroo", "lemur"
        ], 12)

        self.assert_list_in_html("/search?q=query&page=2", "tbody tr", [
            "kangaroo", "lemur"
        ])

    def test_index_requires_api_key(self):
        self.be_admin_oauth_user()
        PrivateKey.get_by_key_name('api').delete()

        response = self.testapp.get('/search?q=query', status=500)
        self.assert_error_page(response)

    def test_ignores_results_for_unknown_packages(self):
        self.mock_results(["armadillo", "mystery_meat", "bandicoot"])

        self.assert_list_in_html("/search?q=query", "tbody tr", [
            "armadillo", "bandicoot"
        ])

    def test_shows_package_metadata(self):
        self.mock_results(["armadillo"])

        response = self.testapp.get("/search?q=query")
        response_text = self.html(response).get_text()
        self.assertIn("armadillo", response_text)
        self.assertIn("1.0.0", response_text)
        self.assertIn("Description for armadillo", response_text)
        self.assert_link(response, "/packages/armadillo")

    def mock_results(self, packages, total_results=None):
        if not total_results: total_results = len(packages)
        """Sets the custom search mock API to return the given packages."""
        def _make_package_result(package):
            return {"link": "http://pub.dartlang.org/packages/" + package}

        search.set_mock_resource({
            "items": [_make_package_result(p) for p in packages],
            "searchInformation": {
                "totalResults": len(packages)
            }
        })
