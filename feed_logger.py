"Load and display many feeds"
import functools
import optparse
import sys
import feedparser


# Helper methods for many of the main loops
def load_urls(filename):
    "load all the feeds from a .lst file"
    for line in open(filename):
        if line.strip():
            yield line.strip()


def load_feed(feed_url):
    "This wrapper exists purely to silence feed loading errors"
    try:
        return feedparser.parse(feed_url)
    except Exception, e:
        print >> sys.stderr, "load", type(e)
        return None


# handler methods
def handler_decorator(func):
    "Decorator to make safe handling easier"
    @functools.wraps(func)
    def handler(feed):
        "Handle any feed, ignoring empty feeds and errors"
        if feed:
            try:
                func(feed)
            except Exception, e:
                print >> sys.stderr, "display", type(e), e
    return handler


@handler_decorator
def display_feed(feed):
    """Dispaly every item in this feed to the termial"""
    for item in feed.entries:
        print item.updated, feed.feed.link, item.title


# single thread syncronus code
def main(filename, handler, count=None):
    """For all feeds in the file handle all
     elements with the handler function"""
    for feed_url in load_urls(filename):
        handler(load_feed(feed_url))


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
                handler(load_feed(feed_url))
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
    for feed in pool.map(load_feed, load_urls(filename)):
        handler(feed)
    pool.close()


def threaded_main(filename, handler, count=3):
    """load all feeds using count threads
       results handled with the handler function

       Used the fact that list.pop is attomic to avoid locking
    """
    import threading
    urls = list(load_urls(filename))

    def thread_of_control():
        while urls:
            try:
                handler(load_feed(urls.pop()))
            except IndexError:
                pass

    for i in range(count):
        threading.Thread(target=thread_of_control).start()
    # as no threads are demons execution continues till compleation


def eventlet_main(filename, handler, count=3):
    import eventlet
    feedparser = eventlet.import_patched('feedparser')

    urls = list(load_urls(filename))

    def load_feed(feed_url):
        "This wrapper exists purly to silence feed loading errors"
        try:
            return feedparser.parse(feed_url)
        except Exception, e:
            print >> sys.stderr, "load", type(e)
            return None

    pool = eventlet.GreenPool(count)
    for feed in pool.imap(load_feed, urls):
        handler(feed)


def queued_main(filename, handler, count=3):
    """load all feeds using count threads
       communicate through queues to avoid both locking and waits

        loadins in count-1 thread, uses last thread for output
    """
    import threading
    import Queue

    def start_demon(func):
        t = threading.Thread(target=func)
        t.daemon = True
        t.start()

    in_queue = Queue.Queue()
    out_queue = Queue.Queue()

    def loader():
        while True:
            item = in_queue.get()
            out_queue.put(load_feed(item))
            in_queue.task_done()

    def writer():
        while True:
            item = out_queue.get()
            handler(item)
            out_queue.task_done()

    for i in range(count-1):
        start_demon(loader)
    start_demon(writer)

    for item in load_urls(filename):
        in_queue.put(item)

    # wait till all feeds are fully processed
    in_queue.join()
    out_queue.join()


def queued_main_two(filename, handler, count=3):
    """load all feeds using count threads
       communicate through queues to avoid both locking and delays

       loadins in count-1 thread, uses last thread for output

       this version uses a higher abstraction (queue consumer thread)
    """
    import threading
    import Queue

    # this would be better at the main level or in a library
    # its only here to make it clear which block of code
    # it is part of
    # this also may be better done by subclassing Thread
    def start_consumer_demon(source, consumer):
        """Start a demon that consumes from source passing each
        item to the consumer"""

        def server():
            """Consume items from source passing each to the consumer
               each task is marked as done before looking for another
            """
            while True:
                item = source.get()
                try:
                    consumer(item)
                except Exception, e:
                    print >> sys.stderr, type(e)
                    print >> sys.stderr, e
                finally:
                    source.task_done()

        t = threading.Thread(target=server)
        t.daemon = True
        t.start()

    in_queue = Queue.Queue()
    out_queue = Queue.Queue()

    for i in range(count-1):
        start_consumer_demon(in_queue, lambda item: out_queue.put(load_feed(item)))

    start_consumer_demon(out_queue, handler)

    for item in load_urls(filename):
        in_queue.put(item)

    # wait till all feeds are fully processed
    in_queue.join()
    out_queue.join()


def queued_main_three(filename, handler, count=3):
    """load all feeds using count threads
       communicate through queues to avoid both locking and delays

       loadins in count-1 thread, uses last thread for output

       this version uses a class as the daemon controller
    """
    import threading
    import Queue

    class Consumer(threading.Thread):
        """A demon thread to read from a queue handling
           each item taken with the consumer method or function
        """
        def __init__(self, source, consumer=None, daemon=True):
            super(ConsumerDemon, self).__init__()
            self.source = source
            self.daemon = daemon
            if consumer:
                self.consumer = consumer

        def run(self):
            while True:
                item = self.source.get()
                try:
                    self.consumer(item)
                except Exception, e:
                    print >> sys.stderr, type(e)
                    print >> sys.stderr, e
                finally:
                    self.source.task_done()

        def consumer(self, item):
            pass

    in_queue = Queue.Queue()
    out_queue = Queue.Queue()

    for i in range(count-1):
        Consumer(in_queue, lambda item: out_queue.put(load_feed(item))).start()

    Consumer(out_queue, handler).start()

    for item in load_urls(filename):
        in_queue.put(item)

    # wait till all feeds are fully processed
    in_queue.join()
    out_queue.join()


if __name__ == '__main__':
    parser = optparse.OptionParser(usage="usage: %prog [options] file1 [file2 ...]", version="%prog 0.1")
    parser.add_option("-n", dest="processes", help="Number of parrallel 'threads'", default=3)

    parser.add_option("-s", dest="main", action="store_const", const=main, help="Simple, non-threaded execution", default=main)
    parser.add_option("-f", dest="main", action="store_const", const=fork_main, help="forked execution")
    parser.add_option("-m", dest="main", action="store_const", const=multyprocess_main, help="multy-proccess execution")
    parser.add_option("-t", dest="main", action="store_const", const=threaded_main, help="threaded execution")
    parser.add_option("-e", dest="main", action="store_const", const=eventlet_main, help="asynchronously (eventlet) execution")
    parser.add_option("-q", dest="main", action="store_const", const=queued_main, help="queued threaded execution")
    parser.add_option("-Q", dest="main", action="store_const", const=queued_main_two, help="cleaner queued threaded execution")
    parser.add_option("-O", dest="main", action="store_const", const=queued_main_three, help="cleaner queued threaded execution")

    parser.add_option("-o", dest="handling", action="store_const", const=display_feed, help="Print breaf descriptions to stdout", default=display_feed)

    options, args = parser.parse_args()
    if args:
        for link in args:
            options.main(link, options.handling, options.processes)
    else:
        parser.error("provide at least one source file")
