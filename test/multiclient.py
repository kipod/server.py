""" Multiplay scenarios test cases.
"""
import json
import unittest
from datetime import datetime
from time import time

from attrdict import AttrDict

from server.db.map import generate_map04, DbMap
from server.db.session import map_session_ctx
from server.defs import Action, Result
from server.entity.event import Event, EventType
from server.game_config import CONFIG
from test.server_connection import ServerConnection


class Test(unittest.TestCase):
    """ Multiplay test cases.
    """
    TIME_SUFFIX = datetime.now().strftime('%H:%M:%S.%f')
    NUM_TOWNS = 4
    PLAYER_NAMES = [
        "Vasya {}".format(TIME_SUFFIX),
        "Petya {}".format(TIME_SUFFIX),
        "Sasha {}".format(TIME_SUFFIX),
        "Dima {}".format(TIME_SUFFIX)
    ]

    def setUp(self):
        self.current_tick = 0
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
        if exp_result == Result.OKEY:
            self.current_tick += 1
        if message:
            return json.loads(message)

    def players_turn(self, players=(), turns_count=1, exp_result=Result.OKEY):
        for _ in range(turns_count):
            for player in players:
                self.turn_no_resp(player)
            for player in players:
                self.turn_check_resp(player, exp_result=exp_result)
            if exp_result == Result.OKEY:
                self.current_tick += 1

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

    def upgrade(self, player, posts=(), trains=(), exp_result=Result.OKEY):
        result, message = self.do_action(
            player, Action.UPGRADE,
            {
                'post': posts,
                'train': trains
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

    def get_post(self, player, post_id, exp_result=Result.OKEY):
        data = self.get_map(player, 1, exp_result=exp_result)
        posts = {x['idx']: x for x in data['post']}
        self.assertIn(post_id, posts)
        return posts[post_id]

    def check_collision_event(self, events, ok_event):
        for event in events:
            if (event['type'] == ok_event.type
                    and event['train'] == ok_event.train
                    and event['tick'] == ok_event.tick):
                return True
        return False

    def test_01(self):
        """ Test play 4 rlayers.
        """
        players_in_game = 4

        player0 = AttrDict(self.login(self.players[0], num_players=players_in_game))
        player1 = AttrDict(self.login(self.players[1], num_players=players_in_game))
        player2 = AttrDict(self.login(self.players[2], num_players=players_in_game))
        player3 = AttrDict(self.login(self.players[3], num_players=players_in_game))

        map_0_0 = self.get_map(self.players[0], 0)
        map_0_1 = self.get_map(self.players[0], 1)

        line_path = (
            [1, 19, 162, 180],
            [2, 38, 143, 179],
            [3, 57, 124, 178],
            [4, 76, 105, 177],
            [5, 95, 86, 176],
            [6, 114, 67, 175],
            [7, 133, 48, 174],
            [8, 152, 29, 173],
            [9, 171, 10, 172]
        )

        for lines in line_path:
            self.move_train(self.players[0], lines[0], player0.train[0].idx, 1)
            self.move_train(self.players[1], lines[1], player1.train[0].idx, 1)
            self.move_train(self.players[2], lines[2], player2.train[0].idx, -1)
            self.move_train(self.players[3], lines[3], player3.train[0].idx, -1)
            self.players_turn(self.players[:players_in_game], turns_count=5)

        for i in range(players_in_game):
            self.logout(self.players[i])
