""" simple client for echo-server
"""
import asyncio
import unittest
from server.defs import SERVER_PORT, Action, Result


@asyncio.coroutine
def send_command(self, action, message, loop):

    self._writer.write(action.to_bytes(4, byteorder='little'))
    if message:
        self._writer.write(len(message).to_bytes(4, byteorder='little'))
        self._writer.write(message.encode('utf-8'))

    data = yield from self._reader.read(4)
    return Result(int.from_bytes(data[0:4], byteorder = 'little'))


@asyncio.coroutine
def connect_to_server(cls):
    cls._loop = asyncio.get_event_loop()
    cls._reader, cls._writer = yield from asyncio.open_connection('127.0.0.1', SERVER_PORT,
                                                                  loop=cls._loop)


def run_in_foreground(task, *, loop=None):
    """Runs event loop in current thread until the given task completes

    Returns the result of the task.
    For more complex conditions, combine with asyncio.wait()
    To include a timeout, combine with asyncio.wait_for()
    """
    if loop is None:
        loop = asyncio.get_event_loop()
    return loop.run_until_complete(asyncio.ensure_future(task, loop=loop))

class TestClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run_in_foreground(connect_to_server(cls))


    @classmethod
    def tearDownClass(cls):
        #print('Close the socket')
        cls._writer.close()
        cls._loop.close()


    def test_send_test_message(self):
        """
        simple test client connection
        """
        result = run_in_foreground(
            send_command(self, Action.LOGIN, 'Boris', asyncio.get_event_loop())
            )
        self.assertEqual(Result.OKEY, result)
        result = run_in_foreground(
            send_command(self, Action.LOGOUT, None, asyncio.get_event_loop())
            )
        self.assertEqual(Result.OKEY, result)
