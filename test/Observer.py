""" test Observer client-server protocol
"""
import unittest
import json
from server.defs import Action, Result
from server.entity.Map import Map
from datetime import datetime
from .ServerConnection import run_in_foreground, ServerConnection
import time


def dict_items(sequence):
            for item in sequence:
                yield item['idx'], item

class TestObserver(unittest.TestCase):
    """ Test class """
    PLAYER_NAME = '-=TEST OBSERVER=-'

    @classmethod
    def setUpClass(cls):
        cls._conn = ServerConnection()

    @classmethod
    def tearDownClass(cls):
        #print('Close the socket')
        del cls._conn

    def test_0_connection(self):
        """ test connection """
        self._conn.verify()

    def do_action(self, action, data):
        return self._conn.do_action(action, data)

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


    def getTrain(self, idx):
        result, message = self.do_action(Action.MAP, {'layer': 1})
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        data = json.loads(message)
        self.assertIn('train', data)
        self.assertGreater(len(data['train']), 0)
        train = {key: value for (key, value) in dict_items(data['train'])}
        self.assertIn(idx, train)
        return train[idx]


    def test_2_observer_select_game(self):
        """ select the test game
            verify initial state
        """
        result, message = self.do_action(Action.GAME, {'idx': 1})
        self.assertEqual(Result.OKEY, result)
        result, message = self.do_action(Action.MAP, {'layer': 0})
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        data = json.loads(message)
        self.assertNotEqual(len(data), 0)
        self.assertIn('line', data)

        self.line = {key: value for (key, value) in dict_items(data['line'])}
        self.assertEqual(self.line[1]["point"][0], 1)
        self.assertEqual(self.line[1]["point"][1], 7)
        train = self.getTrain(0)
        self.assertEqual(train['speed'], 0)
        self.assertEqual(train['line_idx'], 1)
        self.assertEqual(train['position'], 0)

    def set_turn(self, n):
        result, message = self.do_action(Action.TURN, {'idx': n})
        self.assertEqual(Result.OKEY, result)

    def test_3_observer_set_turn(self):
        """ set turn 3 and check position
            set turn 10 and check position
            set turn 0 and check position
            set turn 100 and check position
            set turn -1 and check position
        """
        self.set_turn(3)
        train = self.getTrain(0)
        self.assertEqual(train['speed'], 1)
        self.assertEqual(train['position'], 1)
        self.assertEqual(train['line_idx'], 14)
        self.set_turn(10)
        train = self.getTrain(0)
        self.assertEqual(train['speed'], 1)
        self.assertEqual(train['position'], 1)
        self.assertEqual(train['line_idx'], 18)
        self.set_turn(0)
        train = self.getTrain(0)
        self.assertEqual(train['speed'], 0)
        self.assertEqual(train['position'], 0)
        self.set_turn(100)
        train = self.getTrain(0)
        self.assertEqual(train['speed'], 0)
        self.assertEqual(train['position'], 3)
        self.assertEqual(train['line_idx'], 18)
        self.set_turn(-1)
        train = self.getTrain(0)
        self.assertEqual(train['speed'], 0)
        self.assertEqual(train['position'], 0)


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

    def test_7_game_writes_turns_on_ticks(self):
        """ verify if game on server writes to replay.db
            on game's tick
        """
        conn = ServerConnection()
        result, _ = conn.do_action(Action.LOGIN, {'name': self.PLAYER_NAME})
        self.assertEqual(Result.OKEY, result)
        time.sleep(10)
        result, _ = conn.do_action(Action.LOGOUT, None)
        self.assertEqual(Result.OKEY, result)
        result, message = self.do_action(Action.OBSERVER, None)
        self.assertEqual(Result.OKEY, result)
        games = json.loads(message)
        self.assertIsNotNone(games)
        my_games = [g for g in games if g['name'].count(self.PLAYER_NAME) != 0]
        self.assertGreater(len(my_games), 0)
        # get last my game
        game = my_games[-1]
        self.assertGreater(game['length'], 0)
