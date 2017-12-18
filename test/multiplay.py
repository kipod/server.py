""" Multiplay scenarios test cases.
"""
import json
import unittest
from datetime import datetime
from time import time

from attrdict import AttrDict

from server.db.map import generate_map02, DbMap
from server.db.session import map_session_ctx
from server.defs import Action, Result
from server.game_config import config
from test.server_connection import ServerConnection


class TestMultiplay(unittest.TestCase):
    """ Multiplay test cases.
    """
    TIME_SUFFIX = datetime.now().strftime('%H:%M:%S.%f')
    NUM_TOWNS = 2
    PLAYER_NAMES = [
        "Test Player Name 1 {}".format(TIME_SUFFIX),
        "Test Player Name 2 {}".format(TIME_SUFFIX),
        "Test Player Name 3 {}".format(TIME_SUFFIX)
    ]

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

    def setUp(self):
        self.game_name = "Test Game {}".format(datetime.now().strftime('%H:%M:%S.%f'))
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

    def login(self, player: AttrDict, security_key=None, game_name=None, num_players=None,
              exp_result=Result.OKEY):
        _num_players = self.NUM_TOWNS if num_players is None else num_players
        _game_name = self.game_name if game_name is None else game_name
        result, message = self.do_action(
            player, Action.LOGIN,
            {
                'name': player.name,
                'security_key': security_key,
                'game': _game_name,
                'num_players': _num_players,
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

    def players_turn(self, players=(), turns_count=1, exp_result=Result.OKEY):
        for _ in range(turns_count):
            for player in players:
                self.turn_no_resp(player)
            for player in players:
                self.turn_check_resp(player, exp_result=exp_result)

    def turn_no_resp(self, player):
        player.conn.send_action(Action.TURN, {}, wait_for_response=False)

    def turn_check_resp(self, player, exp_result=Result.OKEY):
        result, message = player.conn.read_response()
        self.assertEqual(exp_result, result)
        if message:
            return json.loads(message)

    def move_train(self, player, line_idx, train_idx, speed, exp_result=Result.OKEY):
        result, message = self.do_action(
            player, Action.MOVE,
            {
                'train_idx': train_idx,
                'speed': speed,
                'line_idx': line_idx
            }
        )
        self.assertEqual(exp_result, result)
        if message:
            return json.loads(message)

    def get_map(self, player, layer, exp_result=Result.OKEY):
        result, message = self.do_action(player, Action.MAP, {'layer': layer})
        self.assertEqual(exp_result, result)
        return json.loads(message)

    def get_train(self, player, train_id, exp_result=Result.OKEY):
        data = self.get_map(player, 1, exp_result=exp_result)
        trains = {x['idx']: x for x in data['train']}
        self.assertIn(train_id, trains)
        return trains[train_id]

    def test_login_and_logout(self):
        """ Test login and logout.
        """
        for player in self.players[:self.NUM_TOWNS]:
            self.login(player)
        for player in self.players[:self.NUM_TOWNS]:
            self.logout(player)

    def test_login_and_turn(self):
        """ Test login one by one and forced turn.
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
            # Ensure that game tick has been forced by players:
            self.assertLess(elapsed, config.TICK_TIME)

        self.logout(self.players[1])
        self.logout(self.players[0])

    def test_players_number(self):
        """ Test login with incorrect 'num_players' value and players overflow.
        """
        message = self.login(self.players[0], num_players=self.NUM_TOWNS + 1, exp_result=Result.BAD_COMMAND)
        self.assertIn('error', message)
        self.assertIn("Unable to create game", message['error'])

        self.login(self.players[0])
        message = self.login(self.players[1], num_players=self.NUM_TOWNS + 1, exp_result=Result.BAD_COMMAND)
        self.assertIn('error', message)
        self.assertIn("Incorrect players number requested", message['error'])

        self.login(self.players[1])
        message = self.login(self.players[2], exp_result=Result.ACCESS_DENIED)
        self.assertIn('error', message)
        self.assertIn("The maximum number of players reached", message['error'])

    def test_move_train_owned_by_other_player(self):
        """ Test movements of train which is owned by other player.
        """
        player0 = AttrDict(self.login(self.players[0]))
        player1 = AttrDict(self.login(self.players[1]))

        # My train:
        self.move_train(self.players[0], 1, player0.train[0].idx, 1)
        # Not my train:
        message = self.move_train(self.players[0], 3, player1.train[0].idx, -1, exp_result=Result.ACCESS_DENIED)
        self.assertIn('error', message)
        self.assertIn("Train's owner mismatch", message['error'])

    def test_train_unload_in_foreign_town(self):
        """ Test train unload in foreign town.
        """
        players_in_game = 2
        player0 = AttrDict(self.login(self.players[0]))
        self.login(self.players[1])

        self.move_train(self.players[0], 1, player0.train[0].idx, 1)
        self.players_turn(self.players[:players_in_game])

        train_before = AttrDict(self.get_train(self.players[0], player0.train[0].idx))

        self.move_train(self.players[0], 7, player0.train[0].idx, 1)
        self.players_turn(self.players[:players_in_game])
        self.move_train(self.players[0], 8, player0.train[0].idx, 1)
        self.players_turn(self.players[:players_in_game], turns_count=2)
        self.move_train(self.players[0], 3, player0.train[0].idx, 1)
        self.players_turn(self.players[:players_in_game], turns_count=2)  # One more turn in town to be sure.

        train_after = AttrDict(self.get_train(self.players[0], player0.train[0].idx))

        self.assertGreater(train_before.goods, 0)
        self.assertEqual(train_before.goods, train_after.goods)
