#! /usr/bin/env python
"Load and display feeds in parallel"
import optparse
import Queue
import sys
import threading
import consumer
import feedparser


def load_urls(filename):
    "load all the feeds from a .lst file"
    for line in open(filename):
        if line.strip():
            yield line.strip()


class LoadFeed(consumer.Filter):
    def __init__(self, source, sink, cap=None):
        super(LoadFeed, self).__init__(source, sink, cap=cap)

    def consumer(self, feed_url):
        return feedparser.parse(feed_url)


def display_feed(feed):
    """Dispaly every item in this feed to the termial"""
    if feed:
        for item in feed.entries:
            try:
                print item.updated, feed.feed.link, item.title
            except Exception, e:
                print >> sys.stderr, "display", type(e), e


def main(feed_links, count=3):
    """load all feeds using count threads
       communicate through queues to avoid both locking and delays
    """
    in_queue = Queue.Queue()
    out_queue = Queue.Queue()
    cap = threading.BoundedSemaphore(count)

    for item in feed_links:
        in_queue.put(item)

    for i in range(count-1):
        LoadFeed(in_queue, out_queue, cap).start()

    consumer.Consumer(out_queue, display_feed, cap).start()
    # wait till all feeds are fully processed
    in_queue.join()
    out_queue.join()


if __name__ == '__main__':
    parser = optparse.OptionParser(usage="usage: %prog [options] file1 [file2 ...]", version="%prog 0.1")
    parser.add_option("-n", dest="processes", help="Number of parrallel 'threads'", default=3)

    options, args = parser.parse_args()
    if args:
        for fn in args:
            print fn
            main(load_urls(fn), options.processes)
    else:
        main(load_urls('feeds.lst'), options.processes)
