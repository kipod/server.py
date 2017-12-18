import json
import unittest
from datetime import datetime

from server.db.map import generate_map02, DbMap
from server.db.session import map_session_ctx
from server.defs import Action, Result
from test.server_connection import ServerConnection


class TestErrors(unittest.TestCase):
    """ Test class for a Game Player.
    """
    PLAYER_NAME = 'Test Player Name ' + datetime.now().strftime('%H:%M:%S.%f')
    SECURITY_KEY = 'you-will-never-guess'

    @classmethod
    def setUpClass(cls):
        database = DbMap()
        database.reset_db()
        with map_session_ctx() as session:
            generate_map02(database, session)

    @classmethod
    def tearDownClass(cls):
        database = DbMap()
        database.reset_db()

    def do_action(self, action, data):
        return self.connection.send_action(action, data)

    def setUp(self):
        self.connection = ServerConnection()
        self.current_tick = 0

    def tearDown(self):
        self.connection.close()

    def login(self, name=None, security_key=SECURITY_KEY, exp_result=Result.OKEY):
        name = self.PLAYER_NAME if name is None else name
        result, message = self.do_action(
            Action.LOGIN,
            {'name': name, 'security_key': security_key}
        )
        self.assertEqual(exp_result, result)
        return json.loads(message)

    def turn(self, turns_count=1, exp_result=Result.OKEY):
        for _ in range(turns_count):
            self.current_tick += 1
            result, _ = self.do_action(Action.TURN, {})
            self.assertEqual(exp_result, result)

    def move_train(self, line_idx, train_idx, speed, exp_result=Result.OKEY):
        result, message = self.do_action(
            Action.MOVE,
            {
                'train_idx': train_idx,
                'speed': speed,
                'line_idx': line_idx
            }
        )
        self.assertEqual(exp_result, result)
        if message:
            return json.loads(message)

    def get_map(self, layer, exp_result=Result.OKEY):
        result, message = self.do_action(Action.MAP, {'layer': layer})
        self.assertEqual(exp_result, result)
        return json.loads(message)

    def test_login(self):
        self.login()
        message = self.login(security_key='incorrect-key', exp_result=Result.ACCESS_DENIED)
        self.assertIn('error', message)
        self.assertIn("Security key mismatch", message['error'])

    def test_get_map(self):
        non_existing_map_layer = 999999
        message = self.get_map(0, exp_result=Result.ACCESS_DENIED)
        self.assertIn('error', message)
        self.assertIn("Login required", message['error'])
        self.login()
        message = self.get_map(non_existing_map_layer, exp_result=Result.RESOURCE_NOT_FOUND)
        self.assertIn('error', message)
        self.assertIn("Map layer not found", message['error'])

    def test_move_train(self):
        test_line_idx = 13
        next_line_idx = 2
        not_connected_line_idx = 10
        non_existing_line_idx = 999999
        non_existing_train_idx = 999999
        player = self.login()
        train_1 = player['train'][0]
        train_2 = player['train'][1]
        train_3 = player['train'][2]

        message = self.move_train(non_existing_line_idx, train_1['idx'], 1, exp_result=Result.RESOURCE_NOT_FOUND)
        self.assertIn('error', message)
        self.assertIn("Line index not found", message['error'])

        message = self.move_train(test_line_idx, non_existing_train_idx, 1, exp_result=Result.RESOURCE_NOT_FOUND)
        self.assertIn('error', message)
        self.assertIn("Train index not found", message['error'])

        self.move_train(test_line_idx, train_1['idx'], 1)
        self.move_train(test_line_idx, train_2['idx'], 1)
        self.turn()
        message = self.move_train(test_line_idx, train_1['idx'], 1, exp_result=Result.BAD_COMMAND)
        self.assertIn('error', message)
        self.assertIn("The train is under cooldown", message['error'])

        self.move_train(test_line_idx, train_3['idx'], 1)
        self.turn()
        self.move_train(test_line_idx, train_3['idx'], 0)
        message = self.move_train(next_line_idx, train_3['idx'], 1, exp_result=Result.BAD_COMMAND)
        self.assertIn('error', message)
        self.assertIn("The train is standing on the line", message['error'])

        self.move_train(test_line_idx, train_3['idx'], 1)
        self.turn()
        message = self.move_train(not_connected_line_idx, train_3['idx'], 1, exp_result=Result.BAD_COMMAND)
        self.assertIn('error', message)
        self.assertIn("The end of the train's line is not connected to the next line", message['error'])

        self.move_train(test_line_idx, train_3['idx'], -1)
        self.turn(turns_count=2)
        message = self.move_train(not_connected_line_idx, train_3['idx'], 1, exp_result=Result.BAD_COMMAND)
        self.assertIn('error', message)
        self.assertIn("The beginning of the train's line is not connected to the next line", message['error'])

        self.move_train(test_line_idx, train_3['idx'], 1)
        self.turn()
        message = self.move_train(not_connected_line_idx, train_3['idx'], 1, exp_result=Result.BAD_COMMAND)
        self.assertIn('error', message)
        self.assertIn("The train is not able to switch the current line to the next line", message['error'])
