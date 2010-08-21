"Load and display many feeds"
import optparse
import feedparser


# Helper methods for many of the main loops
def load_urls(filename):
    "load all the feeds from a .lst file"
    for line in open(filename):
        if line.strip():
            yield line.strip()


def load_feeds(feed_url):
    "This wrapper exists purely to silence feed loading errors"
    try:
        return feedparser.parse(feed_url)
    except Exception, e:
        print >> sys.stderr, "load", type(e)
        return None


# handler methods for recieved feeds
def display_feed(feed):
    """Dispaly every item in this feed to the termial
       ignore invalid feeds
    """
    try:
        for item in feed.entries:
            print item.updated, feed.feed.link, item.title
    except Exception, e:
        print >> sys.stderr, "display", type(e)


# single thread syncronus code
def main(filename, handler, count=None):
    """For all feeds in the file handle all
     elements with the handler function"""
    for feed_url in load_urls(filename):
        handler(load_feeds(feed_url))


#parallel versions of the code
def fork_main(filename, handler, count=3):
    """ Capped forked child processed based off
        http://jacobian.org/writing/python-is-unix/
    """
    import os
    urls = list(load_urls(filename))
    running = 0
    while urls:
        if running < count:
            # if we should make more processes pick an item
            # and fork a process to download it
            running += 1
            feed_url = urls.pop()
            pid = os.fork()
            if pid == 0: #child process - handle one feed and die
                handler(load_feeds(feed_url))
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

       Delays untill all feeds are read before handling
    """
    import multiprocessing

    pool = multiprocessing.Pool(count)
    for feed in pool.map(load_feeds, load_urls(filename)):
        handler(feed)
    pool.close()


def threaded_main(filename, handler, count=3):
    pass


def twisted_main(filename, handler, count=3):
    pass


if __name__ == '__main__':
    parser = optparse.OptionParser(usage="usage: %prog [options] file1 [file2 ...]", version="%prog 0.1")
    parser.add_option("-n", dest="processes", help="Number of parrallel 'threads'", default=3)

    parser.add_option("-s", dest="main", action="store_const", const=main, help="Simple, non-threaded execution", default=main)
    parser.add_option("-f", dest="main", action="store_const", const=fork_main, help="forked execution")
    parser.add_option("-m", dest="main", action="store_const", const=multyprocess_main, help="multy-proccess execution")
    #parser.add_option("-a", dest="main", action="store_const", const=twisted_main, help="async (twisted) execution")
    #parser.add_option("-t", dest="main", action="store_const", const=threaded, help="threaded execution")

    parser.add_option("-o", dest="handling", action="store_const", const=display_feed, help="Print breaf descriptions to stdout", default=display_feed)

    options, args = parser.parse_args()
    if args:
        for link in args:
            options.main(link, options.handling, options.processes)
    else:
        options.main("feeds.lst", options.handling, options.processes)
