""" test python's multithreading
"""

import unittest
import threading
import time


class TestThreads(unittest.TestCase):
    """
    Test-fixture
    Idea: https://habrahabr.ru/post/149420/
    """
    def setUp(self):
        pass


    def tearDown(self):
        pass

    @staticmethod
    def thread_proc(value, event_for_wait, event_for_set):
        """ thread proc
        """
        for _ in xrange(10):
            event_for_wait.wait() # wait for event
            event_for_wait.clear() # clean event for future
            print value
            time.sleep(2)
            event_for_set.set() # set event for neighbor thread


    def test_threads(self):
        """ test threading
        """
        # init events
        event1 = threading.Event()
        event2 = threading.Event()

        #init threads
        thread1 = threading.Thread(target=TestThreads.thread_proc, args=(0, event1, event2))
        thread2 = threading.Thread(target=TestThreads.thread_proc, args=(1, event2, event1))

        #start threads
        thread1.start()
        thread2.start()

        event1.set() # initiate the first event

        # join threads to the main thread
        thread1.join()
        thread2.join()
