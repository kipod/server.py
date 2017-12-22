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


class TestMultiplay(unittest.TestCase):
    """ Multiplay test cases.
    """
    TIME_SUFFIX = datetime.now().strftime('%H:%M:%S.%f')
    NUM_TOWNS = 4
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
            generate_map04(database, session)

    @classmethod
    def tearDownClass(cls):
        database = DbMap()
        database.reset_db()

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

        self.login(self.players[0], num_players=2)
        self.turn(self.players[0], exp_result=Result.NOT_READY)
        self.login(self.players[1], num_players=2)
        self.turn(self.players[0], exp_result=Result.OKEY)  # Waiting for game tick.

        for _ in range(turns_num):
            start = time()
            self.turn_no_resp(self.players[0])
            self.turn_no_resp(self.players[1])
            self.turn_check_resp(self.players[0])
            self.turn_check_resp(self.players[1])
            elapsed = time() - start
            # Ensure that game tick has been forced by players:
            self.assertLess(elapsed, CONFIG.TICK_TIME)

        self.logout(self.players[1])
        with self.assertRaises(Exception):
            self.turn(self.players[1])
        self.turn(self.players[0], exp_result=Result.OKEY)  # Waiting for game tick.
        self.logout(self.players[0])

    def test_players_number(self):
        """ Test login with incorrect 'num_players' value and players overflow.
        """
        message = self.login(self.players[0], num_players=self.NUM_TOWNS + 1, exp_result=Result.BAD_COMMAND)
        self.assertIn('error', message)
        self.assertIn("Unable to create game", message['error'])

        self.login(self.players[0], num_players=2)
        message = self.login(self.players[1], num_players=self.NUM_TOWNS + 1, exp_result=Result.BAD_COMMAND)
        self.assertIn('error', message)
        self.assertIn("Incorrect players number requested", message['error'])

        self.login(self.players[1], num_players=2)
        message = self.login(self.players[2], num_players=2, exp_result=Result.ACCESS_DENIED)
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
        player0 = AttrDict(self.login(self.players[0], num_players=players_in_game))
        self.login(self.players[1], num_players=players_in_game)

        self.move_train(self.players[0], 10, player0.train[0].idx, 1)
        self.players_turn(self.players[:players_in_game], turns_count=3)

        # path to Market
        #10-29-48-58-59-60 51-32-13
        for line_idx in (10, 29, 48, 58, 59, 60):
            self.move_train(self.players[0], line_idx, player0.train[0].idx, 1)
            self.players_turn(self.players[:players_in_game], turns_count=5)

        for line_idx in (51, 32, 13):
            self.move_train(self.players[0], line_idx, player0.train[0].idx, -1)
            self.players_turn(self.players[:players_in_game], turns_count=5)

        train_before = AttrDict(self.get_train(self.players[0], player0.train[0].idx))

        for line_idx in range(4, 10):
            self.move_train(self.players[0], line_idx, player0.train[0].idx, 1)
            self.players_turn(self.players[:players_in_game], turns_count=4)

        train_after = AttrDict(self.get_train(self.players[0], player0.train[0].idx))

        self.assertGreater(train_before.goods, 0)
        self.assertEqual(train_before.goods, train_after.goods)

    def test_upgrade_train_owned_by_other_player(self):
        """ Test upgrade of train which is owned by other player.
        """
        players_in_game = 2
        player0 = AttrDict(self.login(self.players[0], num_players=players_in_game))
        player1 = AttrDict(self.login(self.players[1], num_players=players_in_game))
        town0 = AttrDict(self.get_post(self.players[0], player0.town.idx))
        town1 = AttrDict(self.get_post(self.players[1], player1.town.idx))
        train0 = AttrDict(self.get_train(self.players[0], player0.train[0].idx))
        train1 = AttrDict(self.get_train(self.players[1], player1.train[0].idx))

        # Mine armor for 1-st player:
        # 10-29-48-67-77-78-79-80
        path_line = [10, 29, 48, 67, 77, 78, 79, 80]
        for line_idx in path_line:
            self.move_train(self.players[0], line_idx, train0.idx, 1)
            self.players_turn(self.players[:players_in_game], turns_count=20)

        for line_idx in reversed(path_line):
            self.move_train(self.players[0], line_idx, train0.idx, -1)
            self.players_turn(self.players[:players_in_game], turns_count=5)

        town0_after = AttrDict(self.get_post(self.players[0], player0.town.idx))
        self.assertEqual(town0_after.armor, town0.armor + train0.goods_capacity)

        # Mine armor for 2-nd player:
        # 19-38-57-76 85-84-83-82
        path_line1 = [19, 38, 57, 76]
        path_line2 = [85, 84, 83, 82]
        for line_idx in path_line1:
            self.move_train(self.players[1], line_idx, train1.idx, 1)
            self.players_turn(self.players[:players_in_game], turns_count=5)
        for line_idx in path_line2:
            self.move_train(self.players[1], line_idx, train1.idx, -1)
            self.players_turn(self.players[:players_in_game], turns_count=20)
        for line_idx in reversed(path_line2):
            self.move_train(self.players[1], line_idx, train1.idx, 1)
            self.players_turn(self.players[:players_in_game], turns_count=4)
        for line_idx in reversed(path_line1):
            self.move_train(self.players[1], line_idx, train1.idx, -1)
            self.players_turn(self.players[:players_in_game], turns_count=5)

        town1_after = AttrDict(self.get_post(self.players[1], player1.town.idx))
        self.assertEqual(town1_after.armor, town1.armor + train1.goods_capacity)

        # Upgrade foreign train:
        message = self.upgrade(self.players[0], trains=[train1.idx], exp_result=Result.ACCESS_DENIED)
        self.assertIn('error', message)
        self.assertIn("Train's owner mismatch", message['error'])
        message = self.upgrade(self.players[1], trains=[train0.idx], exp_result=Result.ACCESS_DENIED)
        self.assertIn('error', message)
        self.assertIn("Train's owner mismatch", message['error'])

        # Upgrade not foreign train:
        self.upgrade(self.players[0], trains=[train0.idx])
        self.upgrade(self.players[1], trains=[train1.idx])

    def test_user_events(self):
        """ Test users events independence.
        """
        players_in_game = 2
        player0 = AttrDict(self.login(self.players[0], num_players=players_in_game))
        player1 = AttrDict(self.login(self.players[1], num_players=players_in_game))
        train0 = AttrDict(self.get_train(self.players[0], player0.train[0].idx))
        train1 = AttrDict(self.get_train(self.players[1], player1.train[0].idx))

        # path to Market
        #1-2-3-4
        for line_idx in (1, 2, 3, 4):
            self.move_train(self.players[0], line_idx, train0.idx, 1)
            self.players_turn(self.players[:players_in_game], turns_count=4)

        for line_idx in (9, 8, 7, 6, 5):
            self.move_train(self.players[1], line_idx, train1.idx, -1)
            self.players_turn(self.players[:players_in_game], turns_count=4)

        train0_after = AttrDict(self.get_train(self.players[0], player0.train[0].idx))
        self.assertTrue(
            self.check_collision_event(
                train0_after.event,
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train1.idx)
            )
        )
        self.assertEqual(train0_after.line_idx, train0.line_idx)
        self.assertEqual(train0_after.position, train0.position)

        train1_after = AttrDict(self.get_train(self.players[1], player1.train[0].idx))
        self.assertTrue(
            self.check_collision_event(
                train1_after.event,
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train0.idx)
            )
        )
        self.assertEqual(train1_after.line_idx, train1.line_idx)
        self.assertEqual(train1_after.position, train1.position)
