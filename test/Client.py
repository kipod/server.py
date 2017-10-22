""" simple client for echo-server
"""
import asyncio
import unittest
import json
from server.defs import SERVER_PORT, Action, Result
from server.entity.Map import Map


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
        return Result(int.from_bytes(data[0:4], byteorder='little'))


    @asyncio.coroutine
    def read_message(self):
        data = yield from self._reader.read(4)
        msg_len = int.from_bytes(data[0:4], byteorder='little')
        message = str()
        if msg_len != 0:
            data = yield from self._reader.read(msg_len)
            message = data.decode('utf-8')
        return message


    @asyncio.coroutine
    def connect_to_server(self):
        self._loop = asyncio.get_event_loop()
        self._reader, self._writer = yield from asyncio.open_connection('127.0.0.1', SERVER_PORT,
                                                                loop=self._loop)


class TestClient(unittest.TestCase):

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


    def get_message(self):
        return run_in_foreground(
            self._conn.read_message()
        )

    def test_1_login(self):
        result = self.do_action(
            Action.LOGIN,
            {'name': 'Test Player Name'})
        self.assertEqual(Result.OKEY, result)

    def test_ZZZ_logout(self):
        result = self.do_action(Action.LOGOUT, None)
        self.assertEqual(Result.OKEY, result)


    def test_2_get_map_layer_0(self):
        """
        simple test client connection
        """
        result = self.do_action(Action.MAP, {'layer': 0})
        self.assertEqual(Result.OKEY, result)
        message = self.get_message()
        self.assertNotEqual(len(message), 0)
        map01 = Map()
        map01.from_json_str(message)
        self.assertEqual(len(map01.line), 12)
        self.assertEqual(len(map01.point), 12)


    def test_2_get_map_layer_1(self):
        """
        simple test client connection
        """
        result = self.do_action(Action.LOGIN,
                                {'name': 'Test Player Name'})
        self.assertEqual(Result.OKEY, result)

        result = self.do_action(Action.MAP, {'layer': 1})
        self.assertEqual(Result.OKEY, result)
        message = self.get_message()
        self.assertNotEqual(len(message), 0)
        data = json.loads(message)
        self.assertIn('idx', data.keys())
        self.assertIn('post', data.keys())
        self.assertNotIn('name', data.keys())
        self.assertNotIn('line', data.keys())
        self.assertNotIn('point', data.keys())

