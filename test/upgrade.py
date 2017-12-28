""" Tests for action UPGRADE.
"""

import json
import unittest
from datetime import datetime

from server.db.map import generate_map02, DbMap
from server.db.session import map_session_ctx
from server.defs import Action, Result
from server.game_config import CONFIG
from test.server_connection import ServerConnection


class TestUpgrade(unittest.TestCase):
    """ Test class for a Game Player.
    """
    PLAYER_NAME = 'Test Player Name ' + datetime.now().strftime('%H:%M:%S.%f')

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
        self.player = self.login()
        self.current_tick = 0

    def tearDown(self):
        self.logout()
        self.connection.close()

    def login(self):
        result, message = self.do_action(Action.LOGIN, {'name': self.PLAYER_NAME})
        self.assertEqual(Result.OKEY, result)
        return json.loads(message)

    def logout(self):
        result, _ = self.do_action(Action.LOGOUT, None)
        self.assertEqual(Result.OKEY, result)

    def turn(self, turns_count=1):
        for _ in range(turns_count):
            self.current_tick += 1
            result, _ = self.do_action(Action.TURN, {})
            self.assertEqual(Result.OKEY, result)

    def move_train(self, line_idx, train_idx, speed):
        result, _ = self.do_action(
            Action.MOVE,
            {
                'train_idx': train_idx,
                'speed': speed,
                'line_idx': line_idx
            }
        )
        self.assertEqual(Result.OKEY, result)

    def upgrade(self, posts=(), trains=(), exp_result=Result.OKEY):
        result, _ = self.do_action(
            Action.UPGRADE,
            {
                'post': posts,
                'train': trains
            }
        )
        self.assertEqual(exp_result, result)

    def get_train(self, train_id):
        data = self.get_map(1)
        trains = {x['idx']: x for x in data['train']}
        self.assertIn(train_id, trains)
        return trains[train_id]

    def get_post(self, post_id):
        data = self.get_map(1)
        posts = {x['idx']: x for x in data['post']}
        self.assertIn(post_id, posts)
        return posts[post_id]

    def get_train_line(self, train_id):
        train = self.get_train(train_id)
        return train['line_idx']

    def get_train_speed(self, train_id):
        train = self.get_train(train_id)
        return train['speed']

    def get_map(self, layer):
        result, message = self.do_action(Action.MAP, {'layer': layer})
        self.assertEqual(Result.OKEY, result)
        return json.loads(message)

    def move_train_to_next_line(self, next_line_id, train_idx, speed):
        max_line_lenght = 1000
        self.move_train(next_line_id, train_idx, speed)
        for _ in range(max_line_lenght):
            self.turn()
            if next_line_id == self.get_train_line(train_idx):
                break
        else:
            self.fail("Can't arrive to line: {}".format(next_line_id))

    def move_train_and_go_to_line_end(self, line_idx, train_idx, speed):
        max_line_lenght = 1000
        self.move_train(line_idx, train_idx, speed)
        for _ in range(max_line_lenght):
            self.turn()
            if self.get_train_speed(train_idx) == 0:
                break
        else:
            self.fail("Can't arrive to line end: {}".format(line_idx))

    def test_upgrade_train(self):
        test_line_idx = 18
        town = self.player['town']
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]

        self.move_train_and_go_to_line_end(test_line_idx, train_1['idx'], -1)
        self.move_train_and_go_to_line_end(test_line_idx, train_1['idx'], 1)
        armor = self.get_post(town['idx'])['armor']
        self.assertEqual(armor, town['armor'] + train_1['goods_capacity'])

        armor_to_pay = train_1['next_level_price']
        # Check that player have enough armor to upgrade train:
        self.assertGreaterEqual(armor, armor_to_pay)

        self.upgrade(trains=(train_1['idx'],))
        map_data = self.get_map(1)

        self.assertEqual(self.get_post(town['idx'])['armor'], armor - armor_to_pay)
        self.assertEqual(map_data['train'][0]['level'], train_1['level'] + 1)
        self.assertGreater(map_data['train'][0]['goods_capacity'], train_1['goods_capacity'])
        self.assertGreater(map_data['train'][0]['next_level_price'], train_1['next_level_price'])
        self.assertEqual(map_data['train'][1]['level'], train_2['level'])
        self.assertEqual(map_data['train'][1]['goods_capacity'], train_2['goods_capacity'])
        self.assertEqual(map_data['train'][1]['next_level_price'], train_2['next_level_price'])

    def test_no_upgrade_train_when_no_enough_armor(self):
        town = self.player['town']
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        start_armor = self.get_post(town['idx'])['armor']
        armor_to_pay = train_1['next_level_price']

        # Check that player have no enough armor to upgrade train:
        self.assertLess(start_armor, armor_to_pay)

        self.upgrade(trains=(train_1['idx'],), exp_result=Result.BAD_COMMAND)
        map_data = self.get_map(1)

        self.assertEqual(self.get_post(town['idx'])['armor'], start_armor)
        self.assertEqual(map_data['train'][0]['level'], train_1['level'])
        self.assertEqual(map_data['train'][0]['goods_capacity'], train_1['goods_capacity'])
        self.assertEqual(map_data['train'][0]['next_level_price'], train_1['next_level_price'])
        self.assertEqual(map_data['train'][1]['level'], train_2['level'])
        self.assertEqual(map_data['train'][1]['goods_capacity'], train_2['goods_capacity'])
        self.assertEqual(map_data['train'][1]['next_level_price'], train_2['next_level_price'])

    def test_no_upgrade_if_train_not_in_town_1(self):
        test_line_idx_1 = 18
        test_line_idx_2 = 13
        town = self.player['town']
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]

        self.move_train_and_go_to_line_end(test_line_idx_1, train_1['idx'], -1)
        self.move_train_and_go_to_line_end(test_line_idx_1, train_1['idx'], 1)
        armor = self.get_post(town['idx'])['armor']
        self.assertEqual(armor, town['armor'] + train_1['goods_capacity'])
        self.move_train_and_go_to_line_end(test_line_idx_2, train_1['idx'], 1)

        armor_to_pay = train_1['next_level_price']
        # Check that player have enough armor to upgrade train:
        self.assertGreaterEqual(armor, armor_to_pay)

        self.upgrade(trains=(train_1['idx'],), exp_result=Result.BAD_COMMAND)
        map_data = self.get_map(1)

        self.assertEqual(self.get_post(town['idx'])['armor'], armor)
        self.assertEqual(map_data['train'][0]['level'], train_1['level'])
        self.assertEqual(map_data['train'][0]['goods_capacity'], train_1['goods_capacity'])
        self.assertEqual(map_data['train'][0]['next_level_price'], train_1['next_level_price'])
        self.assertEqual(map_data['train'][1]['level'], train_2['level'])
        self.assertEqual(map_data['train'][1]['goods_capacity'], train_2['goods_capacity'])
        self.assertEqual(map_data['train'][1]['next_level_price'], train_2['next_level_price'])

    def test_no_upgrade_if_train_not_in_town_2(self):
        test_line_idx_1 = 18
        test_line_idx_2 = 1
        town = self.player['town']
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]

        self.move_train_and_go_to_line_end(test_line_idx_1, train_1['idx'], -1)
        self.move_train_and_go_to_line_end(test_line_idx_1, train_1['idx'], 1)
        armor = self.get_post(town['idx'])['armor']
        self.assertEqual(armor, town['armor'] + train_1['goods_capacity'])
        self.move_train_and_go_to_line_end(test_line_idx_2, train_1['idx'], 1)

        armor_to_pay = train_1['next_level_price']
        # Check that player have enough armor to upgrade train:
        self.assertGreaterEqual(armor, armor_to_pay)

        self.upgrade(trains=(train_1['idx'],), exp_result=Result.BAD_COMMAND)
        map_data = self.get_map(1)

        self.assertEqual(self.get_post(town['idx'])['armor'], armor)
        self.assertEqual(map_data['train'][0]['level'], train_1['level'])
        self.assertEqual(map_data['train'][0]['goods_capacity'], train_1['goods_capacity'])
        self.assertEqual(map_data['train'][0]['next_level_price'], train_1['next_level_price'])
        self.assertEqual(map_data['train'][1]['level'], train_2['level'])
        self.assertEqual(map_data['train'][1]['goods_capacity'], train_2['goods_capacity'])
        self.assertEqual(map_data['train'][1]['next_level_price'], train_2['next_level_price'])

    def test_no_upgrade_train_when_no_next_level(self):
        test_line_idx = 18
        wait_for_replenishment = 5
        town = self.player['town']
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]

        for _ in range(len(CONFIG.TRAIN_LEVELS.keys()) - 2):
            self.move_train_and_go_to_line_end(test_line_idx, train_1['idx'], -1)
            self.move_train_and_go_to_line_end(test_line_idx, train_1['idx'], 1)
            self.turn(wait_for_replenishment)

            curr_train_1 = self.get_train(train_1['idx'])
            curr_train_2 = self.get_train(train_2['idx'])
            armor = self.get_post(town['idx'])['armor']
            armor_to_pay = curr_train_1['next_level_price']
            # Check that player have enough armor to upgrade train:
            self.assertGreaterEqual(armor, armor_to_pay)

            self.upgrade(trains=(train_1['idx'],))
            map_data = self.get_map(1)

            self.assertEqual(self.get_post(town['idx'])['armor'], armor - armor_to_pay)
            self.assertEqual(map_data['train'][0]['level'], curr_train_1['level'] + 1)
            self.assertGreater(map_data['train'][0]['goods_capacity'], curr_train_1['goods_capacity'])
            self.assertGreater(map_data['train'][0]['next_level_price'], curr_train_1['next_level_price'])
            self.assertEqual(map_data['train'][1]['level'], curr_train_2['level'])
            self.assertEqual(map_data['train'][1]['goods_capacity'], curr_train_2['goods_capacity'])
            self.assertEqual(map_data['train'][1]['next_level_price'], curr_train_2['next_level_price'])

        # Try to upgrade train to non-existing level:
        self.move_train_and_go_to_line_end(test_line_idx, train_1['idx'], -1)
        self.move_train_and_go_to_line_end(test_line_idx, train_1['idx'], 1)

        curr_train_1 = self.get_train(train_1['idx'])
        curr_train_2 = self.get_train(train_2['idx'])
        armor = self.get_post(town['idx'])['armor']

        self.upgrade(trains=(train_1['idx'],), exp_result=Result.BAD_COMMAND)
        map_data = self.get_map(1)

        self.assertEqual(self.get_post(town['idx'])['armor'], armor)
        self.assertEqual(map_data['train'][0]['level'], curr_train_1['level'])
        self.assertEqual(map_data['train'][0]['goods_capacity'], curr_train_1['goods_capacity'])
        self.assertEqual(map_data['train'][0]['next_level_price'], curr_train_1['next_level_price'])
        self.assertEqual(map_data['train'][1]['level'], curr_train_2['level'])
        self.assertEqual(map_data['train'][1]['goods_capacity'], curr_train_2['goods_capacity'])
        self.assertEqual(map_data['train'][1]['next_level_price'], curr_train_2['next_level_price'])

    def test_upgrade_town(self):
        trips = 20
        test_line_idx = 18
        wait_for_replenishment = 6
        town = self.player['town']
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]

        for _ in range(trips):
            self.move_train_and_go_to_line_end(test_line_idx, train_1['idx'], -1)
            self.move_train_and_go_to_line_end(test_line_idx, train_1['idx'], 1)
            self.turn(wait_for_replenishment)

        armor = self.get_post(town['idx'])['armor']
        self.assertEqual(armor, town['armor_capacity'])
        # Check that player have enough armor to upgrade town:
        self.assertGreaterEqual(armor, town['next_level_price'])

        train_1_partial_unload = self.get_train(train_1['idx'])
        self.upgrade(posts=(town['idx'],))
        self.turn()
        map_data = self.get_map(1)
        town_now = self.get_post(town['idx'])

        self.assertEqual(town_now['armor'], armor - town['next_level_price'] + train_1_partial_unload['goods'])
        self.assertEqual(town_now['level'], town['level'] + 1)
        self.assertGreater(town_now['population_capacity'], town['population_capacity'])
        self.assertGreater(town_now['product_capacity'], town['product_capacity'])
        self.assertGreater(town_now['armor_capacity'], town['armor_capacity'])
        self.assertGreater(town_now['next_level_price'], town['next_level_price'])
        self.assertTrue(
            town_now['train_cooldown'] < town['train_cooldown']
            or town_now['train_cooldown'] == 0
        )

        self.assertEqual(map_data['train'][0]['level'], train_1['level'])
        self.assertEqual(map_data['train'][0]['goods_capacity'], train_1['goods_capacity'])
        self.assertEqual(map_data['train'][0]['next_level_price'], train_1['next_level_price'])
        self.assertEqual(map_data['train'][1]['level'], train_2['level'])
        self.assertEqual(map_data['train'][1]['goods_capacity'], train_2['goods_capacity'])
        self.assertEqual(map_data['train'][1]['next_level_price'], train_2['next_level_price'])

    def test_no_upgrade_town_when_no_enough_armor(self):
        town = self.player['town']
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]

        # Check that player have no enough armor to upgrade town:
        self.assertLess(town['armor'], town['next_level_price'])

        self.upgrade(posts=(town['idx'],), exp_result=Result.BAD_COMMAND)
        map_data = self.get_map(1)
        town_now = self.get_post(town['idx'])

        self.assertEqual(town_now['armor'], town['armor'])
        self.assertEqual(town_now['level'], town['level'])
        self.assertEqual(town_now['population_capacity'], town['population_capacity'])
        self.assertEqual(town_now['product_capacity'], town['product_capacity'])
        self.assertEqual(town_now['armor_capacity'], town['armor_capacity'])
        self.assertEqual(town_now['next_level_price'], town['next_level_price'])
        self.assertEqual(town_now['train_cooldown'], town['train_cooldown'])

        self.assertEqual(map_data['train'][0]['level'], train_1['level'])
        self.assertEqual(map_data['train'][0]['goods_capacity'], train_1['goods_capacity'])
        self.assertEqual(map_data['train'][0]['next_level_price'], train_1['next_level_price'])
        self.assertEqual(map_data['train'][1]['level'], train_2['level'])
        self.assertEqual(map_data['train'][1]['goods_capacity'], train_2['goods_capacity'])
        self.assertEqual(map_data['train'][1]['next_level_price'], train_2['next_level_price'])
