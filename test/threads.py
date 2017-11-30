""" Test python's multithreading.
"""

import threading
import time
import unittest


class TestThreads(unittest.TestCase):
    """ Test-fixture.
    Idea: https://habrahabr.ru/post/149420/
    """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @staticmethod
    def thread_proc(value, event_for_wait, event_for_set):
        """ Thread proc.
        """
        for _ in range(10):
            event_for_wait.wait()  # Wait for event.
            event_for_wait.clear()  # Clean event for future.
            print(value)
            time.sleep(2)
            event_for_set.set()  # Set event for neighbor thread.

    def test_threads(self):
        """ Test threading.
        """
        # Init events.
        event1 = threading.Event()
        event2 = threading.Event()

        # Init threads.
        thread1 = threading.Thread(target=TestThreads.thread_proc, args=(0, event1, event2))
        thread2 = threading.Thread(target=TestThreads.thread_proc, args=(1, event2, event1))

        # Start threads.
        thread1.start()
        thread2.start()

        event1.set()  # Initiate the first event

        # Join threads to the main thread.
        thread1.join()
        thread2.join()
