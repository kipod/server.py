""" Test replay DB helpers.
"""
import unittest
from datetime import datetime

from server.db.models import Game, Action
from server.db.replay import DbReplay, TIME_FORMAT
from server.db.session import ReplaySession
from server.defs import Action as ActionCodes


class TestReplayDb(unittest.TestCase):
    """ Test class.
    """

    PLAYER_NAME = '-=TEST OBSERVER=-'

    def setUp(self):
        self.db = DbReplay()
        self.db.reset_db()
        self.session = ReplaySession()

    def tearDown(self):
        self.db.reset_db()
        self.session.close()

    def test_add_game(self):
        game_name_1 = 'TestGame1'
        game_name_2 = 'TestGame2'
        date_1 = datetime.now()
        date_2 = datetime.now()
        map_name_1 = 'FakeMap1'

        self.db.add_game(game_name_1, map_name_1, date=date_1)
        games = self.session.query(Game).all()
        self.assertEqual(len(games), 1)
        game = games[0]
        self.assertEqual(game.name, game_name_1)
        self.assertEqual(game.date, date_1)
        self.assertEqual(game.map_name, map_name_1)

        self.db.add_game(game_name_2, map_name_1, date=date_2)
        games = self.session.query(Game).all()
        self.assertEqual(len(games), 2)
        game = games[1]
        self.assertEqual(game.name, game_name_2)
        self.assertEqual(game.date, date_2)
        self.assertEqual(game.map_name, map_name_1)

    def test_add_action(self):
        game_id = 1
        code_1 = ActionCodes.LOGIN
        code_2 = ActionCodes.TURN
        message_1 = '{"fake_message": 1}'
        message_2 = '{"fake_message": 2}'
        date_1 = datetime.now()
        date_2 = datetime.now()

        self.db.add_action(code_1, message_1, game_id, date_1)
        actions = self.session.query(Action).all()
        self.assertEqual(len(actions), 1)
        action = actions[0]
        self.assertEqual(action.game_id, game_id)
        self.assertEqual(action.code, code_1)
        self.assertEqual(action.message, message_1)
        self.assertEqual(action.date, date_1)

        self.db.add_action(code_2, message_2, game_id, date_2)
        actions = self.session.query(Action).all()
        self.assertEqual(len(actions), 2)
        action = actions[1]
        self.assertEqual(action.game_id, game_id)
        self.assertEqual(action.code, code_2)
        self.assertEqual(action.message, message_2)
        self.assertEqual(action.date, date_2)

    def test_reset_db(self):
        self.db.add_game('TestGame', 'TestMap')
        self.db.add_action(ActionCodes.LOGIN, '{"test": 1}')

        games = self.session.query(Game).all()
        self.assertEqual(len(games), 1)
        actions = self.session.query(Action).all()
        self.assertEqual(len(actions), 1)

        self.db.reset_db()

        games = self.session.query(Game).all()
        self.assertEqual(len(games), 0)
        actions = self.session.query(Action).all()
        self.assertEqual(len(actions), 0)

    def test_get_all_games(self):
        length = 10
        game_name = 'TestGame1'
        date = datetime.now()
        map_name = 'FakeMap1'

        self.db.add_game(game_name, map_name, date=date)
        self.db.add_action(ActionCodes.LOGIN, '{"message": "fake"}')
        for _ in range(length):
            self.db.add_action(ActionCodes.TURN, None)
        self.db.add_action(ActionCodes.LOGOUT, '{"message": "fake"}')

        games = self.db.get_all_games()
        self.assertEqual(len(games), 1)
        game = games[0]

        self.assertEqual(game['name'], game_name)
        self.assertEqual(game['date'], date.strftime(TIME_FORMAT))
        self.assertEqual(game['map'], map_name)
        self.assertEqual(game['length'], length)

    def test_get_all_actions(self):
        game_id_1 = 1
        game_id_2 = 2
        code = ActionCodes.TURN
        message = '{"fake_message": 1}'
        date = datetime.now()

        self.db.add_action(code, message, game_id_1, date)
        self.db.add_action(code, message, game_id_2, date)

        actions = self.db.get_all_actions(game_id_1)
        self.assertEqual(len(actions), 1)
        action = actions[0]

        self.assertEqual(action['code'], code)
        self.assertEqual(action['message'], message)
        self.assertEqual(action['date'], date.strftime(TIME_FORMAT))

    def test_get_all_games_when_game_have_no_actions(self):
        length = 0
        game_name = 'TestGame1'
        date = datetime.now()
        map_name = 'FakeMap1'

        self.db.add_game(game_name, map_name, date=date)

        games = self.db.get_all_games()
        self.assertEqual(len(games), 1)
        game = games[0]

        self.assertEqual(game['name'], game_name)
        self.assertEqual(game['date'], date.strftime(TIME_FORMAT))
        self.assertEqual(game['map'], map_name)
        self.assertEqual(game['length'], length)
