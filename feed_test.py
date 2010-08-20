"Test the basic import of feeds"
import feed_logger


def test_file_loading():
    """Test the basic load_feeds.
    Should return a generator of valid, stripped urls"""
    filename = "feeds.lst"
    feeds = list(feed_logger.load_feeds(filename))
    print len(feeds)
    assert len(feeds) == 8
    assert feeds[1] == "http://lwn.net/headlines/newrss"


def test_feed_loading():
    "Test that the entries of a url are correctly loaded"
    url = "examplefeed.rss"
    data = list(feed_logger.entries_for_feed(url))
    print len(data)
    assert len(data) == 40


class CountingHandler():
    "Simple stub for a function. Counts how often it's called"
    def __init__(self):
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1


def test_main():
    "Test that the main method of feed_logger works"
    stub_handler = CountingHandler()
    feed_logger.main("test.lst", stub_handler)
    assert stub_handler.count == 40
