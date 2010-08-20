"Load and display many feeds"
import optparse
import feedparser


def load_feeds(filename):
    "load all the feeds from a .lst file"
    for line in open(filename):
        if line.strip():
            yield line.strip()


def entries_for_feed(feed_url):
    """generate all the entries of a rss feed
       broken feeds are swallowed silently.
    """
    try:
        feed = feedparser.parse(feed_url)
        return [(feed_url, item) for item in feed['entries']]
            #yield feed_url, item
    except:
        # Explicitly ignore errors
        pass


def display_item_details(feed, item):
    "Display a brief description this item"
    print item.updated, feed, item.title


def main(filename, handler, _=None):
    """For all feeds in the file handle all
     elements with the handler function"""
    for feed in load_feeds(filename):
        for link, item in entries_for_feed(feed):
            handler(link, item)


def python_is_unix_main(filename, handler, count=3):
    """ Capped forked child processed based off
        http://jacobian.org/writing/python-is-unix/
    """
    import os
    feeds = list(load_feeds(filename))
    running = 0
    while feeds:
        if running < count:
            # if we should make more processes pick and item
            # and fork a process to handle it
            running += 1
            feed = feeds.pop()
            pid = os.fork()
            if pid == 0:
                #child process - handle one feed and die
                for link, item in entries_for_feed(feed):
                    handler(link, item)
                break
        else:
            # if we have enough proccesses already
            # wait for one to end
            os.wait()
            running -= 1
    else:
        # have the main process wait for all children to finish
        while running > 0:
            os.wait()
            running -= 1


def multyprocess_main(filename, handler, count=3):
    """load all feeds over count processes
       then handle all results with the handler function
    """
    import multiprocessing

    pool = multiprocessing.Pool(count)
    for feed in pool.map(entries_for_feed, load_feeds(filename)):
        for link, item in feed:
            handler(link, item)
    pool.close()


def threaded_main(filename, handler, count=3):
    pass


def twisted_main(filename, handler, count=3):
    import twisted.internet



    reactor.run()


if __name__ == '__main__':
    parser = optparse.OptionParser(usage="usage: %prog [options] file1 [file2 ...]", version="%prog 0.1")
    parser.add_option("-p", dest="processes", help="Number of parrallel 'threads'", default=3)

    parser.add_option("-s", dest="main", action="store_const", const=main, help="Simple, non-threaded execution", default=main)
    parser.add_option("-f", dest="main", action="store_const", const=python_is_unix_main, help="forked execution")
    parser.add_option("-m", dest="main", action="store_const", const=multyprocess_main, help="multy-proccess execution")
    #parser.add_option("-a", dest="main", action="store_const", const=twisted_main, help="async (twisted) execution")
    #parser.add_option("-t", dest="main", action="store_const", const=threaded, help="threaded execution")

    options, args = parser.parse_args()
    if args:
        for link in args:
            options.main(link, display_item_details, options.processes)
    else:
        options.main("feeds.lst", display_item_details, options.processes)
