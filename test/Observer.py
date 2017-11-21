""" test Observer client-server protocol
"""
import unittest
import json
from server.defs import Action, Result
from server.entity.Map import Map
from datetime import datetime
from .ServerConnection import run_in_foreground, ServerConnection

class TestObserver(unittest.TestCase):
    """ Test class """

    @classmethod
    def setUpClass(cls):
        cls._conn = ServerConnection()

    @classmethod
    def tearDownClass(cls):
        #print('Close the socket')
        del cls._conn

    def test_0_connection(self):
        """ test connection """
        self.assertIsNotNone(self._conn._loop)
        self.assertIsNotNone(self._conn._reader)
        self.assertIsNotNone(self._conn._writer)

    def do_action(self, action, data):
        return run_in_foreground(
            self._conn.send_action(action, data)
            )

    def test_1_observer_get_game_list(self):
        """ connect as observer
            get list of recorded games
            verify list of games
        """
        result, message = self.do_action(Action.OBSERVER, None)
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        data = json.loads(message)
        self.assertNotEqual(len(data), 0)

    @unittest.skip("not implemented yet")
    def test_5_read_coordinates(self):
        """ get coordinates of points
            using layer 10
        """
        result, message = self.do_action(Action.MAP, {'layer': 10})
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        data = json.loads(message)
        self.assertIn('idx', data.keys())
        self.assertIn('coordinate', data.keys())
        self.assertIn('size', data.keys())
        self.assertNotIn('line', data.keys())
        self.assertNotIn('point', data.keys())



