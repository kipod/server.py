import json
import unittest
from datetime import datetime

from server.db.map import generate_map02, DbMap
from server.db.session import map_session_ctx
from server.defs import Action, Result
from server.entity.event import Event, EventType
from server.game_config import CONFIG
from test.server_connection import ServerConnection


class TestGameEvents(unittest.TestCase):
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

    def get_post(self, post_id):
        data = self.get_map(1)
        posts = {x['idx']: x for x in data['post']}
        self.assertIn(post_id, posts)
        return posts[post_id]

    def get_map(self, layer):
        result, message = self.do_action(Action.MAP, {'layer': layer})
        self.assertEqual(Result.OKEY, result)
        return json.loads(message)

    def check_refugees_arrival_event(self, events, ok_event):
        for event in events:
            if (event['type'] == ok_event.type
                    and event['refugees_number'] == ok_event.refugees_number
                    and event['tick'] == ok_event.tick):
                return True
        return False

    def check_hijackers_assault_event(self, events, ok_event):
        for event in events:
            if (event['type'] == ok_event.type
                    and event['hijackers_power'] == ok_event.hijackers_power
                    and event['tick'] == ok_event.tick):
                return True
        return False

    def check_parasites_assault_event(self, events, ok_event):
        for event in events:
            if (event['type'] == ok_event.type
                    and event['parasites_power'] == ok_event.parasites_power
                    and event['tick'] == ok_event.tick):
                return True
        return False

    def test_refugees_arrival(self):
        turns_num = 6
        refugees_number = 1  # From game config for testing.
        town_idx = self.player['town']['idx']
        turns_ids = [i + 1 for i in range(turns_num)]
        turns_with_refugees = turns_ids[::CONFIG.REFUGEES_COOLDOWN_COEFFICIENT * refugees_number]

        for _ in range(turns_num):
            town = self.get_post(town_idx)
            population_before_turn = town['population']
            self.turn()
            town = self.get_post(town_idx)
            check_event_result = self.check_refugees_arrival_event(
                town['event'],
                Event(EventType.REFUGEES_ARRIVAL, self.current_tick, refugees_number=refugees_number)
            )
            if self.current_tick in turns_with_refugees:
                self.assertTrue(check_event_result)
                self.assertEqual(town['population'], population_before_turn + refugees_number)
            else:
                self.assertFalse(check_event_result)
                self.assertEqual(town['population'], population_before_turn)

    def test_hijackers_assault(self):
        turns_num = 10
        hijackers_power = 1  # From game config for testing.
        refugees_number = 1  # From game config for testing.
        town_idx = self.player['town']['idx']
        turns_ids = [i + 1 for i in range(turns_num)]
        turns_with_assault = turns_ids[::CONFIG.HIJACKERS_COOLDOWN_COEFFICIENT * hijackers_power]
        turns_with_refugees = turns_ids[::CONFIG.REFUGEES_COOLDOWN_COEFFICIENT * refugees_number]

        for _ in range(turns_num):
            town = self.get_post(town_idx)
            armor_before_turn = town['armor']
            population_before_turn = town['population']
            self.turn()
            town = self.get_post(town_idx)
            check_event_result = self.check_hijackers_assault_event(
                town['event'],
                Event(EventType.HIJACKERS_ASSAULT, self.current_tick, hijackers_power=hijackers_power)
            )
            if self.current_tick in turns_with_assault:
                self.assertTrue(check_event_result)
                armor_after_turn = armor_before_turn - hijackers_power
                if armor_after_turn >= 0:
                    self.assertEqual(town['armor'], armor_after_turn)
                    if self.current_tick in turns_with_refugees:
                        self.assertEqual(town['population'], population_before_turn + refugees_number)
                    else:
                        self.assertEqual(town['population'], population_before_turn)
                else:
                    self.assertEqual(town['armor'], 0)
                    if self.current_tick in turns_with_refugees:
                        self.assertEqual(
                            town['population'], max(population_before_turn + refugees_number - hijackers_power, 0))
                    else:
                        self.assertEqual(town['population'], max(population_before_turn - hijackers_power, 0))
            else:
                self.assertFalse(check_event_result)
                self.assertEqual(town['armor'], armor_before_turn)
                if self.current_tick in turns_with_refugees:
                    self.assertEqual(town['population'], population_before_turn + refugees_number)
                else:
                    self.assertEqual(town['population'], population_before_turn)

    def test_parasites_assault(self):
        turns_num = 6
        parasites_power = 1  # From game config for testing.
        town_idx = self.player['town']['idx']
        turns_ids = [i + 1 for i in range(turns_num)]
        turns_with_assault = turns_ids[::CONFIG.PARASITES_COOLDOWN_COEFFICIENT * parasites_power]

        for _ in range(turns_num):
            town = self.get_post(town_idx)
            product_before_turn = town['product']
            population_before_turn = town['population']
            self.turn()
            town = self.get_post(town_idx)
            check_event_result = self.check_parasites_assault_event(
                town['event'],
                Event(EventType.PARASITES_ASSAULT, self.current_tick, parasites_power=parasites_power)
            )
            if self.current_tick in turns_with_assault:
                self.assertTrue(check_event_result)
                self.assertEqual(
                    town['product'], max(product_before_turn - parasites_power - population_before_turn, 0))
            else:
                self.assertFalse(check_event_result)
                self.assertEqual(town['product'], max(product_before_turn - population_before_turn, 0))
