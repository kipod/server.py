""" Multiplay scenarios test cases.
"""
import json
import unittest
from datetime import datetime
from time import time

from attrdict import AttrDict

from server.db.map import generate_map03, DbMap
from server.db.session import map_session_ctx
from server.defs import Action, Result
from server.game_config import config
from test.server_connection import ServerConnection


class TestMultiplay(unittest.TestCase):
    """ Multiplay test cases.
    """
    TIME_SUFFIX = datetime.now().strftime('%H:%M:%S.%f')
    NUM_PLAYERS = 2
    PLAYER_NAMES = [
        "Test Player Name 1 {}".format(TIME_SUFFIX),
        "Test Player Name 2 {}".format(TIME_SUFFIX)
    ]
    GAME_NAME = "Test Game {}".format(TIME_SUFFIX)

    @classmethod
    def setUpClass(cls):
        database = DbMap()
        database.reset_db()
        with map_session_ctx() as session:
            generate_map03(database, session)

    @classmethod
    def tearDownClass(cls):
        database = DbMap()
        database.reset_db()

    def setUp(self):
        self.players = []
        for player_name in self.PLAYER_NAMES:
            conn = ServerConnection()
            player = AttrDict({'name': player_name, 'conn': conn})
            self.players.append(player)

    def tearDown(self):
        for player in self.players:
            player.conn.close()

    @staticmethod
    def do_action(player: AttrDict, action: Action, data=None, is_raw=False):
        return player.conn.send_action(action, data, is_raw=is_raw)

    def login(self, player: AttrDict, security_key=None, exp_result=Result.OKEY):
        result, message = self.do_action(
            player, Action.LOGIN,
            {
                'name': player.name,
                'security_key': security_key,
                'game': self.GAME_NAME,
                'num_players': self.NUM_PLAYERS,
            }
        )
        self.assertEqual(exp_result, result)
        return json.loads(message)

    def logout(self, player, exp_result=Result.OKEY):
        result, message = self.do_action(
            player, Action.LOGOUT, None
        )
        self.assertEqual(exp_result, result)
        if message:
            return json.loads(message)

    def turn(self, player, exp_result=Result.OKEY):
        result, message = self.do_action(player, Action.TURN, {})
        self.assertEqual(exp_result, result)
        if message:
            return json.loads(message)

    def turn_no_resp(self, player):
        player.conn.send_action(Action.TURN, {}, wait_for_response=False)

    def turn_check_resp(self, player, exp_result=Result.OKEY):
        result, message = player.conn.read_response()
        self.assertEqual(exp_result, result)
        if message:
            return json.loads(message)

    def test_login_and_logout(self):
        """ Test login and logout.
        """
        for player in self.players:
            self.login(player)
        for player in self.players:
            self.logout(player)

    def test_login_and_turn(self):
        """ Test login one by one.
        """
        turns_num = 3

        self.login(self.players[0])
        self.turn(self.players[0], exp_result=Result.NOT_READY)
        self.login(self.players[1])
        self.turn(self.players[0], exp_result=Result.OKEY)  # Waiting for game tick.

        for _ in range(turns_num):
            start = time()
            self.turn_no_resp(self.players[0])
            self.turn_no_resp(self.players[1])
            self.turn_check_resp(self.players[0])
            self.turn_check_resp(self.players[1])
            elapsed = time() - start
            self.assertLess(elapsed, config.TICK_TIME)

        self.logout(self.players[0])
        self.logout(self.players[1])
