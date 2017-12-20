# -*- coding: utf-8 -*-
""" Simple client for echo-server.
"""
import json
import unittest
from datetime import datetime

from server.db.map import generate_map02, DbMap
from server.db.session import map_session_ctx
from server.defs import Action, Result
from server.entity.map import Map
from server.game_config import CONFIG
from test.server_connection import ServerConnection


class TestClient(unittest.TestCase):
    """ Test class for a Game Player.
    """
    PLAYER_NAME = 'Test Player Name ' + datetime.now().strftime('%H:%M:%S.%f')

    @classmethod
    def setUpClass(cls):
        database = DbMap()
        database.reset_db()
        with map_session_ctx() as session:
            generate_map02(database, session)
        cls.connection = ServerConnection()

    @classmethod
    def tearDownClass(cls):
        database = DbMap()
        database.reset_db()
        cls.connection.close()

    @classmethod
    def do_action(cls, action, data):
        """ Send action.
        """
        return cls.connection.send_action(action, data)

    @classmethod
    def do_action_raw(cls, action: int, json_str: str):
        """ Send action with raw string data.
        """
        return cls.connection.send_action(action, json_str, is_raw=True)

    def test_1_login(self):
        """ Test login.
        """
        result, message = self.do_action(Action.LOGIN, {'name': self.PLAYER_NAME})
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        data = json.loads(message)
        self.assertIn('idx', data)
        player_id = data['idx']
        self.assertIsNotNone(player_id)

    def test_9_logout(self):
        """ Test logout.
        """
        result, _ = self.do_action(Action.LOGOUT, None)
        self.assertEqual(Result.OKEY, result)

    def test_2_get_map_layer_0(self):
        """ Test layer_to_json_str and from_json_str for layer 0.
        """
        result, message = self.do_action(Action.MAP, {'layer': 0})
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        map_data = json.loads(message)
        self.assertIn('idx', map_data)
        self.assertIn('name', map_data)
        self.assertIn('line', map_data)
        self.assertIn('point', map_data)
        self.assertNotIn('post', map_data)
        self.assertNotIn('train', map_data)
        self.assertNotIn('size', map_data)
        self.assertNotIn('coordinate', map_data)

        map02 = Map()
        map02.from_json_str(message)
        self.assertEqual(len(map02.line), 18)
        self.assertEqual(len(map02.point), 12)

    def test_2_get_map_layer_1(self):
        """ Test layer_to_json_str and from_json_str for layer 1.
        """
        result, message = self.do_action(Action.MAP, {'layer': 1})
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        map_data = json.loads(message)
        self.assertIn('idx', map_data)
        self.assertIn('post', map_data)
        self.assertIn('train', map_data)
        self.assertNotIn('name', map_data)
        self.assertNotIn('line', map_data)
        self.assertNotIn('point', map_data)
        self.assertNotIn('size', map_data)
        self.assertNotIn('coordinate', map_data)

        posts = {x['name']: x for x in map_data['post']}
        self.assertIn('market-small', posts)
        self.assertIn('market-medium', posts)
        self.assertIn('market-big', posts)
        self.assertEqual(posts['market-small']['replenishment'], 1)
        self.assertEqual(posts['market-medium']['replenishment'], 1)
        self.assertEqual(posts['market-big']['replenishment'], 2)

        map02 = Map()
        map02.from_json_str(message)
        self.assertEqual(len(map02.post), 6)
        self.assertEqual(len(map02.train), CONFIG.DEFAULT_TRAINS_COUNT)

    def test_2_get_map_layer_10(self):
        """ Test layer_to_json_str and from_json_str for layer 10.
        """
        result, message = self.do_action(Action.MAP, {'layer': 10})
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        map_data = json.loads(message)
        self.assertIn('idx', map_data)
        self.assertIn('size', map_data)
        self.assertIn('coordinate', map_data)
        self.assertNotIn('post', map_data)
        self.assertNotIn('train', map_data)
        self.assertNotIn('name', map_data)
        self.assertNotIn('line', map_data)
        self.assertNotIn('point', map_data)

        map02 = Map()
        map02.from_json_str(message)
        self.assertEqual(len(map02.size), 2)
        self.assertEqual(len(map02.coordinate), 12)

    def get_train(self, train_id):
        """ Get train by id.
        """
        result, message = self.do_action(Action.MAP, {'layer': 1})
        self.assertEqual(Result.OKEY, result)
        data = json.loads(message)
        trains = {x['idx']: x for x in data['train']}
        self.assertIn(train_id, trains)
        return trains[train_id]

    def get_post(self, post_id):
        """ Get post by id.
        """
        result, message = self.do_action(Action.MAP, {'layer': 1})
        self.assertEqual(Result.OKEY, result)
        data = json.loads(message)
        posts = {x['idx']: x for x in data['post']}
        self.assertIn(post_id, posts)
        return posts[post_id]

    def get_train_pos(self, train_id):
        """ Get train's position.
        """
        train = self.get_train(train_id)
        return train['position']

    def get_train_line(self, train_id):
        """ Get train's current line index.
        """
        train = self.get_train(train_id)
        return train['line_idx']

    def test_3_move_train(self):
        """ Get train belongs to the Player.
        """
        # Login for get player id.
        result, message = self.do_action(Action.LOGIN, {'name': self.PLAYER_NAME})
        self.assertEqual(Result.OKEY, result)
        data = json.loads(message)
        player_id = data['idx']
        n = 0

        train = self.get_train(1)
        self.assertEqual(train['player_id'], player_id)
        # Begin moving.
        self.move_train(1 + n, train['idx'], 1)
        self.turn()
        self.assertGreater(self.get_train_pos(1), 0)

        self.move_to_next_line(7 + n, train['idx'], 1)
        self.move_to_next_line(8 + n, train['idx'], 1)
        self.move_to_next_line(9 + n, train['idx'], 1)
        self.move_to_next_line(10 + n, train['idx'], 1)
        self.move_to_next_line(11 + n, train['idx'], 1)
        self.move_to_next_line(12 + n, train['idx'], 1)
        self.move_to_next_line(1 + n, train['idx'], -1)
        for _ in range(self.get_train_pos(1)):
            self.turn()
        self.assertEqual(self.get_train_pos(1), 0)
        self.assertEqual(self.get_train_line(1), 1)

    def move_train(self, next_line_id, train_idx, speed):
        """ Sends MOVE action.
        """
        result, _ = self.do_action(
            Action.MOVE,
            {
                'train_idx': train_idx,
                'speed': speed,
                'line_idx': next_line_id
            }
        )
        self.assertEqual(Result.OKEY, result)

    def turn(self):
        """ Sends TURN action.
        """
        result, _ = self.do_action(Action.TURN, {})
        self.assertEqual(Result.OKEY, result)

    def move_to_next_line(self, next_line_id, train_idx, speed):
        """ Moves train to the next line.
        """
        # line = self.get_train_line(train_idx)
        self.move_train(next_line_id, train_idx, speed)
        for _ in range(11):
            self.turn()
            if next_line_id == self.get_train_line(train_idx):
                break
        else:
            self.fail("Cant arrive to line: {}".format(next_line_id))

    def test_4_transport_product(self):
        """ Transports product from shop_one to town_one.
        """
        # Login for get player id.
        _, message = self.do_action(Action.LOGIN, {'name': self.PLAYER_NAME})
        data = json.loads(message)
        player_id = data['idx']
        post = self.get_post(1)
        start_product = int(post['product'])

        train = self.get_train(1)
        self.assertEqual(train['player_id'], player_id)
        self.assertEqual(int(train['position']), 0)
        self.assertNotEqual(int(train['goods_capacity']), 0)
        self.assertEqual(int(train['goods']), 0)
        self.assertEqual(int(train['speed']), 0)
        self.move_to_next_line(1, train['idx'], 1)

        train = self.get_train(1)
        while int(train['speed']) != 0:
            self.turn()
            train = self.get_train(1)

        self.assertEqual(int(train['line_idx']), 1)
        self.assertEqual(int(train['position']), 1)
        self.assertEqual(int(train['goods']), 2)

        self.move_to_next_line(1, train['idx'], -1)
        train = self.get_train(1)
        self.assertEqual(int(train['speed']), 0)

        self.assertEqual(int(train['line_idx']), 1)
        self.assertEqual(int(train['position']), 0)
        self.assertEqual(int(train['goods']), 0)
        post = self.get_post(1)
        self.assertEqual(int(post['product']), start_product-4)

    def test_8_wrong_actions(self):
        """ Test error codes on wrong action messages.
        """
        result, _ = self.do_action(Action.LOGIN, {'layer': 10})
        self.assertEqual(Result.BAD_COMMAND, result)
        result, _ = self.do_action_raw(Action.LOGIN, '1234567890')
        self.assertEqual(Result.BAD_COMMAND, result)
