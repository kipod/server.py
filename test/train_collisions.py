import json
import unittest
from datetime import datetime

from server.db.map import generate_map02, DbMap
from server.db.session import map_session_ctx
from server.defs import Action, Result
from server.entity.event import Event, EventType
from test.server_connection import ServerConnection


class TestTrainCollisions(unittest.TestCase):
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

    def move_train(self, line_idx, train_idx, speed, exp_result=Result.OKEY):
        result, _ = self.do_action(
            Action.MOVE,
            {
                'train_idx': train_idx,
                'speed': speed,
                'line_idx': line_idx
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

    def check_collision_event(self, events, ok_event):
        for event in events:
            if (event['type'] == ok_event.type
                    and event['train'] == ok_event.train
                    and event['tick'] == ok_event.tick):
                return True
        return False

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

    def test_collision_in_same_position_move_about(self):
        test_line_idx = 13
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train(test_line_idx, train_1['idx'], 1)
        self.move_train(test_line_idx, train_2['idx'], 1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])

    def test_collision_in_same_position_move_towards(self):
        test_line_idx = 13
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train_and_go_to_line_end(test_line_idx, train_1['idx'], 1)
        self.move_train(test_line_idx, train_1['idx'], -1)
        self.move_train(test_line_idx, train_2['idx'], 1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])

    def test_collision_on_line_with_stopped_1(self):
        test_line_idx = 13
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train(test_line_idx, train_1['idx'], 1)
        self.turn()
        self.move_train(test_line_idx, train_1['idx'], 0)
        self.turn()
        self.move_train(test_line_idx, train_2['idx'], 1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])

    def test_collision_on_line_with_stopped_2(self):
        test_line_idx = 13
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train_and_go_to_line_end(test_line_idx, train_1['idx'], 1)
        self.move_train(test_line_idx, train_2['idx'], 1)
        self.turn()
        self.move_train(test_line_idx, train_2['idx'], 0)
        self.turn()
        self.move_train(test_line_idx, train_1['idx'], -1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])

    def test_collision_goods_destroyed(self):
        test_line_idx = 1
        town_idx = self.player['town']['idx']
        start_product = self.player['town']['product']
        population = self.player['town']['population']
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train_and_go_to_line_end(test_line_idx, train_1['idx'], 1)
        self.move_train(test_line_idx, train_1['idx'], -1)
        self.move_train(test_line_idx, train_2['idx'], 1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])
        self.assertEqual(map_data['train'][0]['goods'], 0)
        self.assertEqual(map_data['train'][1]['goods'], 0)
        # No new product arrived:
        self.assertEqual(self.get_post(town_idx)['product'], start_product - population * self.current_tick)

    def test_collision_in_point_1(self):
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train_and_go_to_line_end(13, train_1['idx'], 1)
        self.move_train_and_go_to_line_end(1, train_2['idx'], 1)
        self.move_train_and_go_to_line_end(7, train_2['idx'], 1)
        self.move_train(2, train_2['idx'], 1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])

    def test_collision_in_point_2(self):
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train_and_go_to_line_end(13, train_1['idx'], 1)
        self.move_train(13, train_2['idx'], 1)
        self.turn(2)
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])

    def test_collision_in_post_1(self):
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train_and_go_to_line_end(1, train_1['idx'], 1)
        self.move_train(1, train_2['idx'], 1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])

    def test_collision_in_post_2(self):
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        self.move_train_and_go_to_line_end(1, train_1['idx'], 1)
        self.move_train_and_go_to_line_end(13, train_2['idx'], 1)
        self.move_train_and_go_to_line_end(2, train_2['idx'], -1)
        self.move_train(7, train_2['idx'], -1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])

    def test_no_collision_in_town(self):
        self.turn()
        map_data = self.get_map(1)
        self.assertEqual(map_data['train'][0]['event'], [])
        self.assertEqual(map_data['train'][1]['event'], [])

    def test_collision_with_3_trains(self):
        test_line_idx = 13
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]
        train_3 = self.player['train'][2]
        self.move_train(test_line_idx, train_1['idx'], 1)
        self.move_train(test_line_idx, train_2['idx'], 1)
        self.move_train(test_line_idx, train_3['idx'], 1)
        self.turn()
        map_data = self.get_map(1)
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][0]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_3['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][1]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_3['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][2]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_1['idx'])
            )
        )
        self.assertTrue(
            self.check_collision_event(
                map_data['train'][2]['event'],
                Event(EventType.TRAIN_COLLISION, self.current_tick, train=train_2['idx'])
            )
        )
        self.assertEqual(map_data['train'][0]['line_idx'], train_1['line_idx'])
        self.assertEqual(map_data['train'][0]['position'], train_1['position'])
        self.assertEqual(map_data['train'][1]['line_idx'], train_2['line_idx'])
        self.assertEqual(map_data['train'][1]['position'], train_2['position'])
        self.assertEqual(map_data['train'][2]['line_idx'], train_3['line_idx'])
        self.assertEqual(map_data['train'][2]['position'], train_3['position'])

    def test_cooldown_on_collision(self):
        test_line_idx = 13
        town = self.get_post(self.player['town']['idx'])
        train_1 = self.player['train'][0]
        train_2 = self.player['train'][1]

        self.assertEqual(train_1['cooldown'], 0)
        self.assertEqual(train_2['cooldown'], 0)

        self.move_train(test_line_idx, train_1['idx'], 1)
        self.move_train(test_line_idx, train_2['idx'], 1)
        self.turn()

        for i in range(town['train_cooldown_on_collision']):
            map_data = self.get_map(1)
            self.assertEqual(map_data['train'][0]['cooldown'], town['train_cooldown_on_collision'] - i)
            self.assertEqual(map_data['train'][1]['cooldown'], town['train_cooldown_on_collision'] - i)
            self.move_train(test_line_idx, train_1['idx'], 1, exp_result=Result.BAD_COMMAND)
            self.move_train(test_line_idx, train_2['idx'], 1, exp_result=Result.BAD_COMMAND)
            self.turn()
        else:
            map_data = self.get_map(1)
            self.assertEqual(map_data['train'][0]['cooldown'], 0)
            self.assertEqual(map_data['train'][1]['cooldown'], 0)
            self.move_train(test_line_idx, train_1['idx'], 1, exp_result=Result.OKEY)
            self.move_train(test_line_idx, train_2['idx'], 1, exp_result=Result.OKEY)
