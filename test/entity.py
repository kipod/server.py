""" Test server entities.
"""
import json
import unittest

from server.db.map import generate_map02, DbMap
from server.db.session import map_session_ctx
from server.entity.map import Map
from server.entity.player import Player
from server.entity.point import Point
from server.entity.post import Post, PostType
from server.entity.train import Train
from server.game_config import CONFIG


class TestEntity(unittest.TestCase):

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
        pass

    def tearDown(self):
        pass

    def test_map_init(self):
        """ Test create map entity.
        """
        game_map = Map(CONFIG.MAP_NAME)
        train = Train(idx=1, line_idx=game_map.line[1].idx, position=0)
        game_map.add_train(train)

        self.assertTrue(game_map.okey)
        self.assertEqual(len(game_map.line), 18)
        self.assertEqual(len(game_map.point), 12)
        self.assertNotEqual(game_map.size, (None, None))
        self.assertEqual(len(game_map.coordinate), len(game_map.point))
        self.assertEqual(len(game_map.post), 6)
        self.assertEqual(len(game_map.train), 1)

    def test_map_serialization(self):
        """ Test Map entity serialization/deserialization.
        """
        game_map = Map(CONFIG.MAP_NAME)
        train = Train(idx=1, line_idx=game_map.line[1].idx, position=0)
        game_map.add_train(train)

        str_json = game_map.layer_to_json_str(0)
        data = json.loads(str_json)
        self.assertIn('name', data)
        self.assertIn('line', data)
        self.assertIn('point', data)
        self.assertIn('idx', data)
        self.assertNotIn('post', data)
        self.assertNotIn('train', data)
        self.assertNotIn('size', data)
        self.assertNotIn('coordinate', data)

        new_map = Map()
        new_map.from_json_str(str_json)
        self.assertEqual(new_map.name, game_map.name)
        self.assertEqual(new_map.idx, game_map.idx)
        self.assertEqual(len(new_map.line), 18)
        self.assertEqual(len(new_map.point), 12)
        self.assertEqual(new_map.size, (None, None))
        self.assertEqual(len(new_map.coordinate), 0)
        self.assertEqual(len(new_map.post), 0)
        self.assertEqual(len(new_map.train), 0)

        str_json = game_map.layer_to_json_str(1)
        data = json.loads(str_json)
        self.assertNotIn('name', data)
        self.assertNotIn('line', data)
        self.assertNotIn('point', data)
        self.assertNotIn('size', data)
        self.assertNotIn('coordinate', data)
        self.assertIn('idx', data)
        self.assertIn('post', data)
        self.assertIn('train', data)

        new_map = Map()
        new_map.from_json_str(str_json)
        self.assertEqual(new_map.name, None)
        self.assertEqual(new_map.idx, game_map.idx)
        self.assertEqual(len(new_map.line), 0)
        self.assertEqual(len(new_map.point), 0)
        self.assertEqual(new_map.size, (None, None))
        self.assertEqual(len(new_map.coordinate), 0)
        self.assertEqual(len(new_map.post), 6)
        self.assertEqual(len(new_map.train), 1)

        str_json = game_map.layer_to_json_str(10)
        data = json.loads(str_json)
        self.assertNotIn('name', data)
        self.assertNotIn('line', data)
        self.assertNotIn('point', data)
        self.assertNotIn('post', data)
        self.assertNotIn('train', data)
        self.assertIn('idx', data)
        self.assertIn('size', data)
        self.assertIn('coordinate', data)

        new_map = Map()
        new_map.from_json_str(str_json)
        self.assertEqual(new_map.name, None)
        self.assertEqual(new_map.idx, game_map.idx)
        self.assertEqual(len(new_map.line), 0)
        self.assertEqual(len(new_map.point), 0)
        self.assertNotEqual(new_map.size, (None, None))
        self.assertEqual(len(new_map.coordinate), 12)
        self.assertEqual(len(new_map.post), 0)
        self.assertEqual(len(new_map.train), 0)

    def test_player_init(self):
        """ Test create player entity.
        """
        player_name = 'Vasya'
        player = Player.create(player_name)
        train = Train(idx=1, line_idx=1, position=0)
        point = Point(idx=1, post_id=1)
        post = Post(idx=1, name='test-post', post_type=PostType.TOWN, point_id=point.idx)

        player.set_home(point, post)
        player.add_train(train)

        self.assertNotEqual(player.idx, None)
        self.assertEqual(player.name, player_name)
        self.assertIn(train.idx, player.train)
        self.assertEqual(player.train[train.idx].player_id, player.idx)
        self.assertIs(player.home, point)
        self.assertIs(player.town, post)

        new_player = Player.create(player_name)
        self.assertEqual(player.idx, new_player.idx)

    def test_player_serialization(self):
        """ Test Player entity serialization/deserialization.
        """
        player1 = Player.create('Vasya')
        train = Train(idx=1, line_idx=1, position=0)
        point = Point(idx=1, post_id=1)
        post = Post(idx=1, name='test-post', post_type=PostType.TOWN, point_id=point.idx)
        player1.set_home(point, post)
        player1.add_train(train)
        str_data = player1.to_json_str()

        player2 = Player.create(None)
        player2.from_json_str(str_data)

        self.assertEqual(player1.idx, player2.idx)
        self.assertEqual(player1.name, player2.name)
        self.assertEqual(player1.home.idx, player2.home.idx)
        self.assertEqual(player1.town.idx, player2.town.idx)
        self.assertEqual([t for t in player1.train], [t for t in player2.train])
