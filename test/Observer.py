""" Test Observer client-server protocol.
"""
import json
import time
import unittest

from server.defs import Action, Result
from server.entity.game import Game
from test.ServerConnection import ServerConnection


def dict_items(sequence):
            for item in sequence:
                yield item['idx'], item


class TestObserver(unittest.TestCase):
    """ Test class.
    """

    PLAYER_NAME = '-=TEST OBSERVER=-'

    @classmethod
    def setUpClass(cls):
        cls._conn = ServerConnection()

    @classmethod
    def tearDownClass(cls):
        # print('Close the socket')
        del cls._conn

    def test_0_connection(self):
        """ Test connection.
        """
        self._conn.verify()

    def do_action(self, action, data):
        return self._conn.do_action(action, data)

    def test_1_observer_get_game_list(self):
        """ Connect as observer, get list of recorded games, verify list of games.
        """
        result, message = self.do_action(Action.OBSERVER, None)
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        data = json.loads(message)
        self.assertNotEqual(len(data), 0)

    def get_train(self, idx):
        result, message = self.do_action(Action.MAP, {'layer': 1})
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        data = json.loads(message)
        self.assertIn('trains', data)
        self.assertGreater(len(data['trains']), 0)
        trains = {x['idx']: x for x in data['trains']}
        self.assertIn(idx, trains)
        return trains[idx]

    def test_2_observer_select_game(self):
        """ Select the test game, verify initial state.
        """
        result, message = self.do_action(Action.GAME, {'idx': 1})
        self.assertEqual(Result.OKEY, result)
        result, message = self.do_action(Action.MAP, {'layer': 0})
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        data = json.loads(message)
        self.assertNotEqual(len(data), 0)
        self.assertIn('lines', data)

        lines = {key: value for (key, value) in dict_items(data['lines'])}
        self.assertEqual(lines[1]['point'][0], 1)
        self.assertEqual(lines[1]['point'][1], 7)
        train = self.get_train(0)
        self.assertEqual(train['speed'], 0)
        self.assertEqual(train['line_idx'], 1)
        self.assertEqual(train['position'], 0)

    def set_turn(self, n):
        result, message = self.do_action(Action.TURN, {'idx': n})
        self.assertEqual(Result.OKEY, result)

    def test_3_observer_set_turn(self):
        """ Set turn 3 and check position,
        set turn 10 and check position,
        set turn 0 and check position,
        set turn 100 and check position,
        set turn -1 and check position.
        """
        self.set_turn(3)
        train = self.get_train(0)
        self.assertEqual(train['speed'], 1)
        self.assertEqual(train['position'], 1)
        self.assertEqual(train['line_idx'], 14)
        self.set_turn(10)
        train = self.get_train(0)
        self.assertEqual(train['speed'], 1)
        self.assertEqual(train['position'], 1)
        self.assertEqual(train['line_idx'], 18)
        self.set_turn(0)
        train = self.get_train(0)
        self.assertEqual(train['speed'], 0)
        self.assertEqual(train['position'], 0)
        self.set_turn(100)
        train = self.get_train(0)
        self.assertEqual(train['speed'], 0)
        self.assertEqual(train['position'], 3)
        self.assertEqual(train['line_idx'], 18)
        self.set_turn(-1)
        train = self.get_train(0)
        self.assertEqual(train['speed'], 0)
        self.assertEqual(train['position'], 0)

    def test_5_read_coordinates(self):
        """ Get coordinates of points using layer 10.
        """
        result, message = self.do_action(Action.MAP, {'layer': 10})
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        data = json.loads(message)
        self.assertIn('idx', data.keys())
        self.assertIn('coordinates', data.keys())
        self.assertIn('size', data.keys())
        self.assertNotIn('lines', data.keys())
        self.assertNotIn('points', data.keys())

    def test_7_game_writes_turns_on_ticks(self):
        """ Verify if game on server writes to replay.db on game's tick.
        """
        conn = ServerConnection()
        result, _ = conn.do_action(Action.LOGIN, {'name': self.PLAYER_NAME})
        self.assertEqual(Result.OKEY, result)
        time.sleep(Game.TICK_TIME + 1)  # Wait for game tick.
        result, _ = conn.do_action(Action.LOGOUT, None)
        self.assertEqual(Result.OKEY, result)
        time.sleep(1)  # Wait for DB commit.
        result, message = self.do_action(Action.OBSERVER, None)
        self.assertEqual(Result.OKEY, result)
        games = json.loads(message)
        self.assertIsNotNone(games)
        my_games = [g for g in games if g['name'].count(self.PLAYER_NAME) != 0]
        self.assertGreater(len(my_games), 0)
        # Get last my game.
        game = my_games[-1]
        self.assertGreater(game['length'], 0)
