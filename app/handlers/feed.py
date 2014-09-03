from feedgen.feed import FeedGenerator

import handlers
from handlers.pager import QueryPager
from models.package import Package


def generate_feed(page=1):
    feed = FeedGenerator()
    feed.title("Pub Packages")
    feed.link("https://pub.dartlang.org/")
    feed.author("Dart Team")
    i = 1
    pager = QueryPager(page, "/packages.atom?page=%d",
                       Package.all().order('-updated'),
                       per_page=10)
    for item in pager.get_items():
        i += 1
        entry = feed.add_entry()
        for author in item.latest_version.pubspec.authors:
            entry.author(author)
        entry.link(item.url)
        entry.description(item.latest_version.pubspec.get("description", "Not Available"))
        entry.content(item.latest_version.readme.render())
        entry.published(item.updated)
        entry.updated(item.updated)

    return feed.atom_str(pretty=True)