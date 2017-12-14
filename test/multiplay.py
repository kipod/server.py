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

    PLAYER = {name: {'name': name, 'conn': None} for name in PLAYER_NAME}

    GAME_NAME = "Test Game {}".format(TIME_SUFFIX)

    @classmethod
    def setUpClass(cls):
        # with DbMap() as database:
        #     database.reset_db()
        #     generate_map03(database)
        for player in cls.PLAYER.values():
            player['conn'] = ServerConnection()

    @classmethod
    def tearDownClass(cls):
        # with DbMap() as database:
        #     database.reset_db()
        pass

    @classmethod
    def do_action(cls, player_name: str, action: Action, data={}):
        """ Send action.
        """
        return cls.PLAYER[player_name]['conn'].do_action(action, data)

    # @classmethod
    # def do_action_raw(cls, action: int, json_str: str):
    #     """ Send action with raw string data.
    #     """
    #     return cls.connection.do_action_raw(action, json_str)

    def test_00_connection(self):
        """ Test connection.
        """
        for player in self.PLAYER.values():
            conn = player['conn']
            self.assertIsNotNone(conn._loop)
            self.assertIsNotNone(conn._reader)
            self.assertIsNotNone(conn._writer)

    def test_99_logout(self):
        """ Test logout.
        """
        for player in self.PLAYER_NAME:
            result, _ = self.do_action(player, Action.LOGOUT, None)
            self.assertEqual(Result.OKEY, result)

    def test_01_login(self):
        """ Test login.
        """

        result, message = self.do_action(self.PLAYER_NAME[0], Action.LOGIN,
                                         {
                                             'name': self.PLAYER_NAME[0],
                                             'game': self.GAME_NAME,
                                             'num_players': 2
                                         })
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        data = json.loads(message)
        self.assertIn('idx', data)
        player_id = data['idx']
        self.assertIsNotNone(player_id)

        result, _ = self.do_action(self.PLAYER_NAME[0], Action.TURN)
        self.assertEqual(Result.NOT_READY, result)

        result, message = self.do_action(self.PLAYER_NAME[1], Action.LOGIN,
                                         {
                                             'name': self.PLAYER_NAME[1],
                                             'game': self.GAME_NAME,
                                             'num_players': 2
                                         })
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        data = json.loads(message)
        self.assertIn('idx', data)
        player_id = data['idx']
        self.assertIsNotNone(player_id)

    def test_02_turn(self):
        """ test turn 2 players """
        result, _ = self.do_action(self.PLAYER_NAME[0], Action.TURN)
        self.assertEqual(Result.TIMEOUT, result)
        result, _ = self.do_action(self.PLAYER_NAME[1], Action.TURN)
        self.assertEqual(Result.OKEY, result)



