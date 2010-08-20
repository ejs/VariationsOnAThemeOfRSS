"Load and display many feeds"
import optparse
import feedparser


def load_feeds(filename):
    "load all the feeds from a .lst file"
    for line in open(filename):
        if line.strip():
            yield line.strip()


def entries_for_feed(feed_url):
    "generate all the entries of a rss feed"
    try:
        feed = feedparser.parse(feed_url)
        for item in feed['entries']:
            yield item
    except:
        # Explicitly ignore errors
        pass


def display_item_details(feed, item):
    "Display a brief description this item"
    print item.updated, feed, item.title


def simple_main(filename, handler, _=None):
    """For all feeds in the file handle all
     elements with the handler function"""
    for feed in load_feeds(filename):
        for item in entries_for_feed(feed):
            handler(feed, item)


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("-p", dest="processes", help="Number of parrallel 'threads'", default=3)

    options, args = parser.parse_args()
    main = simple_main
    if args:
        for link in args:
            main(link, display_item_details, options.processes)
    else:
        main("feeds.lst", display_item_details, options.processes)
