from feedgen.feed import FeedGenerator

import handlers
from handlers.pager import QueryPager
from models.package import Package
import cherrypy

XML_BEGIN = '<?xml version="1.0" encoding="UTF-8"?>'

class Feeds(object):
    """Generation of Feeds"""
    def generate_feed(self, page=1):
        feed = FeedGenerator()
        feed.id("https://pub.dartlang.org/feed.atom")
        feed.title("Pub Packages for Dart")
        feed.link(href="https://pub.dartlang.org/", rel="alternate")
        feed.description("Last Updated Packages")
        feed.author({"name": "Dart Team"})
        i = 1
        pager = QueryPager(int(page), "/feed.atom?page=%d",
                       Package.all().order('-updated'),
                       per_page=10)
        for item in pager.get_items():
            i += 1
            entry = feed.add_entry()
            for author in item.latest_version.pubspec.authors:
                entry.author({ "name": author })
            entry.title("v" + item.latest_version.pubspec.get("version") + " of " + item.name)
            entry.link(item.url)
            entry.id("https://pub.dartlang.org/packages/" + item.name + "#" + item.latest_version.pubspec.get("version"))
            entry.description(
                item.latest_version.pubspec
                    .get("description", "Not Available"))
            entry.content(item.latest_version.readme.render())
            entry.published(item.updated)
            entry.updated(item.updated)
        return feed
    
    def atom(self, page=1):
        cherrypy.response.headers['Content-Type'] = "application/atom+xml"
        return XML_BEGIN + "\n" + self.generate_feed(page=page).atom_str(pretty=True)
