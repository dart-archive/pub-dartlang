# Copyright (c) 2014, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import json
import logging
import re
import urllib

from apiclient.discovery import build

import handlers
from handlers.pager import Pager
from models.package import Package
from models.private_key import PrivateKey

# The custom search ID for pub.dartlang.org.
CUSTOM_SEARCH_ID = "009011925481577436976:h931xn2j7o0"

PACKAGE_URL_PATTERN = re.compile(
    r'https?://pub\.dartlang\.org/packages/([a-z0-9_]+)')

RESULTS_PER_PAGE = 10

# The Custom Search API limits to 100 results and generates an error if
# we request beyond that.
MAX_RESULTS = 100

# The Custom Search Client API service. This will be lazily initialized the
# first time it is used.
_search_service = None

# This is set by set_mock_resource() so that the tests do not hit the actual
# Custom Search API.
_mock_resource = None

def set_mock_resource(resource):
    """Set this to mock the Custom Search API.

    After calling this, instead of calling the actual Custom Search API, the
    given resources will be used as the result of the API call.
    """
    global _mock_resource
    _mock_resource = resource

class Search(object):
    """The handler for /search.

    Calls the Custom Search API and formats and displays the results. The
    search is filtered to only include URLs within pub.dartlang.org/packages,
    which are the kind of results.

    However, since the Google spider only crawls pub periodically, the results
    are often out of date. The result snippet may describe an older version of
    the package. To avoid that, and to provide a more nicely integrated design,
    we perform the search on the server using the Google client API.

    We then take those results and look through the result URLs. For each one,
    we get the package it's for and then look up the live metadata for the
    latest version of that package directly from the data store. Then we render
    the result ourselves.
    """

    @handlers.requires_api_key
    def index(self, q, page=1):
        """Format and display a list of search results.

        Arguments:
          q: The search query to perform.
          page: The page of results to get. Each page contains 10 results.
        """
        page = int(page)

        results, count = self._query_search(q, page)
        pager = SearchPager(page, q, count)

        return handlers.render("search",
             query=q,
             hasResults=len(results) != 0,
             results=results,
             pagination=pager.render_pagination(),
             layout={'title': 'Search Results for "' + q + '"'})

    def _query_search(self, query, page):
        """Call the Custom Search API with the given query and get the given
        page of results.

        Return a tuple. The first element is the list of search results for the
        requested page. Each result is a map that can be passed to the search
        result template. The second element is the total count of search
        results. The count will always be the total count of all results
        starting from the beginning, regardless of the page being requested.

        For each search result, this looks up the actual package in the data
        store and returns its live metadata. If the URL cannot be parsed or
        the package cannot be found in the datastore, it is not included in the
        results.

        Arguments:
          query: The search query to perform.
          page: The page of results to return. If out of bounds, returns an
            empty collection of results.
        """
        global _search_service

        if page < 1 or page > MAX_RESULTS / RESULTS_PER_PAGE:
            handlers.http_error(400, "Page \"%d\" is out of bounds." % page)

        start = (page - 1) * RESULTS_PER_PAGE + 1

        results = []
        if _mock_resource:
            resource = _mock_resource
        else:
            if not _search_service:
                _search_service = build("customsearch", "v1",
                                        developerKey=PrivateKey.get_api())
            resource = _search_service.cse().list(q=query, cx=CUSTOM_SEARCH_ID,
                num=RESULTS_PER_PAGE, start=start).execute()

        if "items" in resource:
            for item in resource["items"]:
                result = self._get_result(item)
                if result: results.append(result)

        count = int(resource["searchInformation"]["totalResults"])
        return results, count

    def _get_result(self, resource_item):
        """Convert a Custom Search API result into a map of package metadata
        that can be rendered.

        If the result does not reference a valid package, return None.

        Arguments:
          resource_item: The API result. It is expected to be a map containing
            a "link" key which will likely be a package URL.
        """
        link = resource_item["link"]
        match = PACKAGE_URL_PATTERN.match(link)
        if not match:
            logging.warning('could not parse search result URL "%s"' % link)
            return None

        package = Package.get_by_key_name(match.group(1))
        if not package:
            logging.warning('could not find search result package "%s"' %
                match.group(1))
            return None

        return {
            "name": package.name,
            "version": package.latest_version.version,
            "desc": package.ellipsized_description,
            "url": "/packages/" + package.name,
            "last_uploaded": package.latest_version.relative_created
        }


class SearchPager(Pager):
    """A class for paginating a Google Custom Search API call."""

    def __init__(self, page, query, count):
        """Create a new SearchPager.

        Arguments:
          page: The page of entities to get. One-based.
          href_pattern: The href for links to a given page. This should use "%d"
            where the page number should go.
          query: The Query object for the entities to paginate.
          per_page: The number of entities to display on each page.
          max_pages: The maximum number of pages to display individually in the
            pagination control.
        """

        self._query = query
        self._count = count
        href_pattern = "/search?q=" + urllib.quote_plus(query) + "&page=%d"
        super(SearchPager, self).__init__(page, href_pattern,
                                          per_page=RESULTS_PER_PAGE)

    def _get_count(self, max_item_to_count):
        return min(self._count, max_item_to_count, MAX_RESULTS)
