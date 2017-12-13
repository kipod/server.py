""" Multiplay scenarios test cases
"""
import json
import unittest
from datetime import datetime

from test.server_connection import ServerConnection
from server.db.map import generate_map03, DbMap

from server.defs import Action, Result

class TestMultiplay(unittest.TestCase):
    """ Multiplay test cases
    """
    TIME_SUFFIX = datetime.now().strftime('%H:%M:%S.%f')
    PLAYER_NAME = [
        "Test Player Name 0 {}".format(TIME_SUFFIX),
        "Test Player Name 1 {}".format(TIME_SUFFIX)
    ]

    GAME_NAME = "Test Game {}".format(TIME_SUFFIX)

    @classmethod
    def setUpClass(cls):
        # with DbMap() as database:
        #     database.reset_db()
        #     generate_map03(database)
        cls.connection = []
        for _ in cls.PLAYER_NAME:
            cls.connection.append(ServerConnection())

    @classmethod
    def tearDownClass(cls):
        # with DbMap() as database:
        #     database.reset_db()
        del cls.connection

    @classmethod
    def do_action(cls, connection_idx: int, action: Action, data):
        """ Send action.
        """
        return cls.connection[connection_idx].do_action(action, data)

    # @classmethod
    # def do_action_raw(cls, action: int, json_str: str):
    #     """ Send action with raw string data.
    #     """
    #     return cls.connection.do_action_raw(action, json_str)

    def test_00_connection(self):
        """ Test connection.
        """
        for conn in self.connection:
            self.assertIsNotNone(conn._loop)
            self.assertIsNotNone(conn._reader)
            self.assertIsNotNone(conn._writer)

    def test_01_login(self):
        """ Test login.
        """
        result, message = self.do_action(0, Action.LOGIN,
                                         {
                                             'name': self.PLAYER_NAME[0],
                                             'game': self.GAME_NAME,
                                             'num_players': 1
                                         })
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        data = json.loads(message)
        self.assertIn('idx', data)
        player_id = data['idx']
        self.assertIsNotNone(player_id)
