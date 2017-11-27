# -*- coding: utf-8 -*-
""" simple client for echo-server
"""
import unittest
import json
from server.defs import Action, Result
from server.entity.Map import Map
from datetime import datetime
from .ServerConnection import run_in_foreground, ServerConnection

class TestClient(unittest.TestCase):
    """ Test class for a Game Player"""
    PLAYER_NAME = 'Test Player Name ' + datetime.now().strftime('%H:%M:%S.%f')

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

    def test_1_login(self):
        result, message = self.do_action(
            Action.LOGIN,
            {'name': self.PLAYER_NAME})
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        data = json.loads(message)
        self.assertIn('idx', data)
        player_id = data['idx']
        self.assertIsNotNone(player_id)

    def test_9_logout(self):
        """ game over """
        result, _ = self.do_action(Action.LOGOUT, None)
        self.assertEqual(Result.OKEY, result)


    def test_2_get_map_layer_0(self):
        """
        simple test client connection
        """
        result, message = self.do_action(Action.MAP, {'layer': 0})
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        map01 = Map()
        map01.from_json_str(message)
        self.assertEqual(len(map01.line), 18)
        self.assertEqual(len(map01.point), 12)


    def test_2_get_map_layer_1(self):
        """
        simple test client connection
        """
        result, message = self.do_action(Action.MAP, {'layer': 1})
        self.assertEqual(Result.OKEY, result)
        self.assertNotEqual(len(message), 0)
        data = json.loads(message)
        self.assertIn('idx', data.keys())
        self.assertIn('post', data.keys())
        self.assertNotIn('name', data.keys())
        self.assertNotIn('line', data.keys())
        self.assertNotIn('point', data.keys())


    def get_train(self, train_id):
        """ get train by id """
        result, message = self.do_action(Action.MAP, {'layer': 1})
        self.assertEqual(Result.OKEY, result)
        data = json.loads(message)
        train = {x['idx']: x for x in data['train']}
        self.assertIn(train_id, train)
        return train[train_id]


    def get_post(self, post_id):
        """ get train by id """
        result, message = self.do_action(Action.MAP, {'layer': 1})
        self.assertEqual(Result.OKEY, result)
        data = json.loads(message)
        return data['post'][post_id]


    def get_train_pos(self, train_id):
        """ get train's position """
        train = self.get_train(train_id)
        return train['position']


    def get_train_line(self, train_id):
        """ get train's current line index """
        train = self.get_train(train_id)
        return train['line_idx']

    def test_3_move_train(self):
        """
        get train belongs to the Player
        """
        # login for get player id
        _, message = self.do_action(Action.LOGIN, {'name': self.PLAYER_NAME})
        data = json.loads(message)
        player_id = data['idx']
        N = 0

        train = self.get_train(0)
        self.assertEqual(train['player_id'], player_id)
        # begin moving
        result, _ = self.do_action(Action.MOVE, {
            'train_idx': train['idx'],
            'speed': 1,
            'line_idx': 1+N})
        self.assertEqual(Result.OKEY, result)
        result, _ = self.do_action(Action.TURN, {})
        self.assertEqual(Result.OKEY, result)
        self.assertGreater(self.get_train_pos(0), 0)

        self.move_to_next_line(7+N, train['idx'], 1)
        self.move_to_next_line(8+N, train['idx'], 1)
        self.move_to_next_line(9+N, train['idx'], 1)
        self.move_to_next_line(10+N, train['idx'], 1)
        self.move_to_next_line(11+N, train['idx'], 1)
        self.move_to_next_line(12+N, train['idx'], 1)
        self.move_to_next_line(1+N, train['idx'], -1)
        for _ in range(self.get_train_pos(0)):
            result, _ = self.do_action(Action.TURN, {})
            self.assertEqual(Result.OKEY, result)
        self.assertEqual(self.get_train_pos(0), 0)
        self.assertEqual(self.get_train_line(0), 1)

    def move_train(self, next_line_id, train_idx, speed):
        """ send move action """
        result, _ = self.do_action(Action.MOVE, {
            'train_idx': train_idx,
            'speed': speed,
            'line_idx': next_line_id})
        self.assertEqual(Result.OKEY, result)

    def turn(self):
        """ TURN action """
        result, _ = self.do_action(Action.TURN, {})
        self.assertEqual(Result.OKEY, result)

    def move_to_next_line(self, next_line_id, train_idx, speed):
        """ move train to the next line """
        # line = self.get_train_line(train_idx)
        self.move_train(next_line_id, train_idx, speed)
        for _ in range(11):
            self.turn()
            if next_line_id == self.get_train_line(train_idx):
                break
        else:
            self.fail("Cant arrive to line:{}".format(next_line_id))

    def test_4_transport_product(self):
        """
        transport product from shop_one to town_one
        """
        # login for get player id
        _, message = self.do_action(Action.LOGIN, {'name': self.PLAYER_NAME})
        data = json.loads(message)
        player_id = data['idx']
        post = self.get_post(0)
        start_product = int(post['product'])

        train = self.get_train(0)
        self.assertEqual(train['player_id'], player_id)
        self.assertEqual(int(train['position']), 0)
        self.assertNotEqual(int(train['capacity']), 0)
        self.assertEqual(int(train['product']), 0)
        self.assertEqual(int(train['speed']), 0)
        self.move_to_next_line(1, train['idx'], 1)

        train = self.get_train(0)
        while int(train['speed']) != 0:
            result, _ = self.do_action(Action.TURN, {})
            self.assertEqual(Result.OKEY, result)
            train = self.get_train(0)

        self.assertEqual(int(train['line_idx']), 1)
        self.assertEqual(int(train['position']), 1)
        self.assertEqual(int(train['product']), 2)

        self.move_to_next_line(1, train['idx'], -1)
        train = self.get_train(0)
        while int(train['speed']) != 0:
            result, _ = self.do_action(Action.TURN, {})
            self.assertEqual(Result.OKEY, result)
            train = self.get_train(0)

        self.assertEqual(int(train['line_idx']), 1)
        self.assertEqual(int(train['position']), 0)
        self.assertEqual(int(train['product']), 0)
        post = self.get_post(0)
        self.assertEqual(int(post['product']), start_product-2)

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

    def test_7_train_come_to_shop_map_l1_check_train_pos(self):
        """
        когда train приезжает в shop, и снова спрашивается layer1, train меняет position =0
        """
        # login for get player id
        result, message = self.do_action(Action.LOGIN, {'name': self.PLAYER_NAME})
        self.assertEqual(Result.OKEY, result)
        data = json.loads(message)
        player_id = data['idx']
        post = self.get_post(0)
        start_product = int(post['product'])
        train = self.get_train(0)
        self.assertEqual(train['player_id'], player_id)
        self.move_train(1, 0, 1)
        for _ in range(11):
            position = self.get_train(0)['position']
            if position == 1:
                break
            self.turn()
        self.assertEqual(position, 1)
        position = self.get_train(0)['position']
        self.assertEqual(position, 1)

