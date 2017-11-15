""" simple client for echo-server
"""
import asyncio
import unittest
import json
import time
from server.defs import SERVER_PORT, Action, Result
from server.entity.Map import Map

SERVER_ADDR = '127.0.0.1'
#SERVER_ADDR = 'wgforge-srv.wargaming.net'
#SERVER_PORT = 80


def run_in_foreground(task, *, loop=None):
    """Runs event loop in current thread until the given task completes

    Returns the result of the task.
    For more complex conditions, combine with asyncio.wait()
    To include a timeout, combine with asyncio.wait_for()
    """
    if loop is None:
        loop = asyncio.get_event_loop()
    return loop.run_until_complete(asyncio.ensure_future(task, loop=loop))


class ServerConnection(object):
    def __init__(self):
        self._loop = None
        self._reader = None
        self._writer = None
        run_in_foreground(self.connect_to_server())

    def __del__(self):
        self._writer.close()
        self._loop.close()

    @asyncio.coroutine
    def send_action(self, action, data, loop=asyncio.get_event_loop()):
        self._writer.write(action.to_bytes(4, byteorder='little'))
        if not data is None:
            message = json.dumps(data, sort_keys=True, indent=4)
            self._writer.write(len(message).to_bytes(4, byteorder='little'))
            self._writer.write(message.encode('utf-8'))

        data = yield from self._reader.read(4)
        result = Result(int.from_bytes(data[0:4], byteorder='little'))
        data = yield from self._reader.read(4)
        msg_len = int.from_bytes(data[0:4], byteorder='little')
        message = str()
        if msg_len != 0:
            data = yield from self._reader.read(msg_len)
            message = data.decode('utf-8')
        return result, message


    @asyncio.coroutine
    def connect_to_server(self):
        self._loop = asyncio.get_event_loop()
        self._reader, self._writer = yield from asyncio.open_connection(SERVER_ADDR, SERVER_PORT,
                                                                        loop=self._loop)


class TestClient(unittest.TestCase):

    PLAYER_NAME = 'Test Player Name'

    @classmethod
    def setUpClass(self):
        self._conn = ServerConnection()

    @classmethod
    def tearDownClass(self):
        #print('Close the socket')
        del self._conn

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


    def test_ZZZ_logout(self):
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
        self.assertEqual(len(map01.line), 12)
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
        return data['train'][train_id]


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

        result, message = self.do_action(Action.MAP, {'layer': 1})
        self.assertEqual(Result.OKEY, result)
        data = json.loads(message)
        self.assertIn('train', data)
        trains = data['train']
        self.assertNotEqual(0, len(trains))
        train = trains[0]
        self.assertEqual(train['player_id'], player_id)
        # begin moving
        result, _ = self.do_action(Action.MOVE, {
            'train_idx': train['idx'],
            'speed': 1,
            'line_idx': 1})
        self.assertEqual(Result.OKEY, result)
        result, _ = self.do_action(Action.TURN, {})
        self.assertEqual(Result.OKEY, result)
        self.assertGreater(self.get_train_pos(0), 0)

        self.move_to_next_line(7, train['idx'], 1)
        self.move_to_next_line(8, train['idx'], 1)
        self.move_to_next_line(9, train['idx'], 1)
        self.move_to_next_line(10, train['idx'], 1)
        self.move_to_next_line(11, train['idx'], 1)
        self.move_to_next_line(12, train['idx'], 1)
        self.move_to_next_line(1, train['idx'], -1)
        self.move_to_next_line(1, train['idx'], 0)
        for _ in range(self.get_train_pos(0)):
            result, _ = self.do_action(Action.TURN, {})
            self.assertEqual(Result.OKEY, result)
        self.assertEqual(self.get_train_pos(0), 0)
        self.assertEqual(self.get_train_line(0), 1)


    def move_to_next_line(self, next_line_id, train_idx, speed):
        """ move train to the next line """
        result, _ = self.do_action(Action.MOVE, {
            'train_idx': train_idx,
            'speed': speed,
            'line_idx': next_line_id})
        self.assertEqual(Result.OKEY, result)
        for _ in range(11):
            result, _ = self.do_action(Action.TURN, {})
            self.assertEqual(Result.OKEY, result)
            if next_line_id == self.get_train_line(train_idx):
                break
        else:
            self.assertTrue(False, "Cant arrive to line:{}".format(next_line_id))


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
        self.assertEqual(int(train['position']), 10)
        self.assertEqual(int(train['product']), int(train['capacity']))

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
        self.assertEqual(int(post['product']), start_product+15)


