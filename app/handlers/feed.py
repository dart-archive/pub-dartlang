from feedgen.feed import FeedGenerator

import handlers
from handlers.pager import QueryPager
from models.package import Package
import cherrypy


class Feeds(object):
    """Generation of Feeds"""
    def generate_feed(self, page=1):
        feed = FeedGenerator()
        feed.id("https://pub.dartlang.org/feeds/updated")
        feed.title("Pub Packages")
        feed.link(href="https://pub.dartlang.org/", rel="alternate")
        feed.description("Last Updated Packages")
        feed.author({"name": "Dart Team", "email": "misc@dartlang.org"})
        i = 1
        pager = QueryPager(int(page), "/packages.atom?page=%d",
                       Package.all().order('-updated'),
                       per_page=10)
        for item in pager.get_items():
            i += 1
            entry = feed.add_entry()
            for author in item.latest_version.pubspec.authors:
                entry.author({ "name": author, "email": "N/A", uri: "" })
            entry.link(item.url)
            entry.id("https://pub.dartlang.org/feeds")
            entry.description(item.latest_version.pubspec.get("description", "Not Available"))
            entry.content(item.latest_version.readme.render())
            entry.published(item.updated)
            entry.updated(item.updated)
        return feed
    
    def atom(self, page=1):
        return self.generate_feed(page=page).atom_str(pretty=True)

    def rss(self, page=1):
        return self.generate_feed(page=page).rss_str(pretty=True)