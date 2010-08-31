import sys
import threading


class Consumer(threading.Thread):
    """A thread to read from a queue handling
       each item taken with the consumer method or function
    """
    def __init__(self, source, consumer=None, cap=None, daemon=True):
        super(Consumer, self).__init__()
        self.source = source
        self.daemon = daemon
        self.cap = cap or threading.BoundedSemaphore()
        if consumer:
            self.consumer = consumer

    def __enter__(self):
        # This ordering avoids race conditions by allowing
        # the option of slightly more than the requested number
        # of threads to run for a short period of time
        item = self.source.get()
        self.cap.acquire()
        return item

    def __exit__(self, type, value, traceback):
        if type != None:
            print >> sys.stderr, type, value
        self.source.task_done()
        self.cap.release()
        return True # supress any exception

    def run(self):
        while True:
            with self as item:
                self.consumer(item)

    def consumer(self, item):
        pass


class Filter(Consumer):
    def __init__(self, source, sink, filter=None, cap=None, daemon=True):
        super(Filter, self).__init__(source, filter, cap, daemon)
        self.sink = sink

    def run(self):
        while True:
            with self as item:
                result = self.consumer(item)
                self.sink.put(result)
