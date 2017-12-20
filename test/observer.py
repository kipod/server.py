""" Test Observer client-server protocol.
"""
import json
import time
import unittest

from server.db.map import DbMap, generate_map03
from server.db.replay import DbReplay, generate_replay01
from server.db.session import map_session_ctx, replay_session_ctx
from server.defs import Action, Result
from server.game_config import CONFIG
from test.server_connection import ServerConnection


def dict_items(sequence):
            for item in sequence:
                yield item['idx'], item


class TestObserver(unittest.TestCase):
    """ Test class.
    """

    PLAYER_NAME = '-=TEST OBSERVER=-'

    @classmethod
    def setUpClass(cls):
        cls.connection = ServerConnection()
        cls.prepare_db()

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()
        cls.reset_db()

    @staticmethod
    def prepare_db():
        """ Prepare replay DB and map DB for tests.
        """
        replay_db = DbReplay()
        replay_db.reset_db()
        with replay_session_ctx() as session:
            generate_replay01(replay_db, session)

        map_db = DbMap()
        map_db.reset_db()
        with map_session_ctx() as session:
            generate_map03(map_db, session)

    @staticmethod
    def reset_db():
        """ Resets replay DB and map DB after tests.
        """
        replay_db = DbReplay()
        replay_db.reset_db()

        map_db = DbMap()
        map_db.reset_db()

    def do_action(self, action, data):
        return self.connection.send_action(action, data)

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
        self.assertIn('train', data)
        self.assertGreater(len(data['train']), 0)
        trains = {x['idx']: x for x in data['train']}
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
        self.assertIn('line', data)

        lines = {key: value for (key, value) in dict_items(data['line'])}
        self.assertEqual(lines[1]['point'][0], 1)
        self.assertEqual(lines[1]['point'][1], 2)
        train = self.get_train(1)
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
        train = self.get_train(1)
        self.assertEqual(train['speed'], 1)
        self.assertEqual(train['position'], 3)
        self.assertEqual(train['line_idx'], 1)
        self.set_turn(10)
        train = self.get_train(1)
        self.assertEqual(train['speed'], 1)
        self.assertEqual(train['position'], 2)
        self.assertEqual(train['line_idx'], 3)
        self.set_turn(0)
        train = self.get_train(1)
        self.assertEqual(train['speed'], 0)
        self.assertEqual(train['position'], 0)
        self.set_turn(100)
        train = self.get_train(1)
        self.assertEqual(train['speed'], -1)
        self.assertEqual(train['position'], 1)
        self.assertEqual(train['line_idx'], 176)
        self.set_turn(-1)
        train = self.get_train(1)
        self.assertEqual(train['speed'], 0)
        self.assertEqual(train['position'], 0)
        self.set_turn(1000)
        train = self.get_train(1)
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
        self.assertIn('coordinate', data.keys())
        self.assertIn('size', data.keys())
        self.assertNotIn('line', data.keys())
        self.assertNotIn('point', data.keys())

    def test_7_game_writes_turns_on_ticks(self):
        """ Verify if game on server writes to replay.db on game's tick.
        """
        conn = ServerConnection()
        result, _ = conn.send_action(Action.LOGIN, {'name': self.PLAYER_NAME})
        self.assertEqual(Result.OKEY, result)
        time.sleep(CONFIG.TICK_TIME + 1)  # Wait for game tick.
        result, _ = conn.send_action(Action.LOGOUT, None)
        self.assertEqual(Result.OKEY, result)
        time.sleep(2)  # Wait for DB commit.
        result, message = self.do_action(Action.OBSERVER, None)
        self.assertEqual(Result.OKEY, result)
        games = json.loads(message)
        self.assertIsNotNone(games)
        my_games = [g for g in games if g['name'].count(self.PLAYER_NAME) != 0]
        self.assertGreater(len(my_games), 0)
        # Get last my game.
        game = my_games[-1]
        self.assertGreater(game['length'], 0)
