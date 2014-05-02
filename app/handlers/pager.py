# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import math

import handlers
import cherrypy

class Pager(object):
    """An abstract class for pagination.

    A new pager should be initialized for each page that is to be displayed. It
    determines which elements will be displayed and renders the pagination
    control.
    """

    def __init__(self, page, href_pattern, per_page=10, max_pages=15):
        """Create a new Pager.

        Arguments:
          page: The page of entities to get. One-based.
          href_pattern: The href for links to a given page. This should use "%d"
            where the page number should go.
          per_page: The number of entities to display on each page.
          max_pages: The maximum number of pages to display individually in the
            pagination control.
        """

        self._page = page
        self._href_pattern = href_pattern
        self._per_page = per_page
        self._max_pages = max_pages

        # If there are many pages, we don't want to individually list all of
        # them. These are the minimum and maximum page numbers that we do want
        # to list.
        min_page_to_list = self._page - self._max_pages / 2
        max_page_to_list = self._page + self._max_pages / 2

        # If we're close enough to the first page that we show fewer than
        # `max_pages/2` pages to the left of the current page, re-allocate the
        # extra space to the right.
        if min_page_to_list < 1:
            max_page_to_list += 1 - min_page_to_list
            min_page_to_list = 1

        max_item_to_count = max_page_to_list * per_page

        # Count one extra page so we can know if there are more pages to the
        # right of those we're displaying.
        count = self._get_count(max_item_to_count)
        self._more_pages = count > max_item_to_count
        if self._more_pages:
            count -= 1
        else:
            # As above, if we're close enough to the last page, re-allocate
            # extra space to the left.
            min_page_to_list -= (max_item_to_count - count) / per_page
            min_page_to_list = max(1, min_page_to_list)

        self._min_page = min_page_to_list
        self._max_page = max_page_to_list
        self._page_count = int(math.ceil(float(count) / self._per_page))

    def _get_count(self, max_item_to_count):
        """Gets the total number of results for the query.

        Arguments:
          max_item_to_count: The maximum number of results to count. If a
            number larger than this is returned, then the pager will show that
            there are more results beyond the known count using "...".
        """
        raise NotImplementedError("Subclass must implement _get_count()")

    def render_pagination(self):
        """Return the HTML for the pagination control."""
        return handlers.render("pagination", page_links=self._page_links,
                               layout=False)

    @property
    def page_count(self):
        """The total number of pages."""
        return self._page_count

    @property
    def prev_url(self):
        """The URL for the previous page, or None if this is the first page."""
        if self._page == 1: return None
        return cherrypy.request.base + (self._href_pattern % (self._page - 1))

    @property
    def next_url(self):
        """The URL for the next page, or None if this is the last page."""
        if self._page == self._page_count: return None
        return cherrypy.request.base + (self._href_pattern % (self._page + 1))

    @property
    def _page_links(self):
        """Return a list of Link objects for the pagination control."""
        yield Pager.Link(self._href_pattern, "&laquo;", self._page - 1,
                         disabled=(self._page == 1))

        if self._min_page != 1:
            yield Pager.Link(self._href_pattern, "...", self._min_page - 1)

        for i in xrange(self._min_page, self._page_count + 1):
            yield Pager.Link(self._href_pattern, str(i), i,
                             active=(i == self._page))

        if self._more_pages:
            yield Pager.Link(self._href_pattern, "...", self._max_page + 1)

        yield Pager.Link(self._href_pattern, "&raquo;", self._page + 1,
                         disabled=(self._page == self._page_count))

    class Link(object):
        """An object representing a single link in the pagination control."""

        def __init__(self, href_pattern, text, page, active=False,
                     disabled=False):
            """Create a new page link.

            Arguments:
              href_pattern: The pattern used to generate a link to this page.
              text: The text of the link.
              page: The page number that the link points to.
              active: Whether the link represents the current page.
              disabled: Whether the link is invalid.
            """

            self.href_pattern = href_pattern
            self.text = text
            self.page = page
            self.state = None
            if active: self.state = "active"
            if disabled: self.state = "disabled"

        @property
        def href(self):
            """The location of the link."""
            if self.state is not None: return None
            return self.href_pattern % self.page

class QueryPager(Pager):
    """A class for paginating a model.

    A new pager should be initialized for each page that is to be displayed. It
    determines which entities will be displayed and renders the pagination
    control.
    """

    def __init__(self, page, href_pattern, query, per_page=10, max_pages=15):
        """Create a new QueryPager.

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
        super(QueryPager, self).__init__(page, href_pattern, per_page=per_page,
                                         max_pages=max_pages)

    def get_items(self):
        """Return a list of entities for the current page."""
        offset = (self._page - 1) * self._per_page
        return self._query.fetch(self._per_page, offset)

    def _get_count(self, max_item_to_count):
        return self._query.count(limit=max_item_to_count + 1)
