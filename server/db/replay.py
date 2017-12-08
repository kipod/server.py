""" Replay DB helpers.
"""
import sys
from datetime import datetime

from invoke import task
from sqlalchemy import func, and_

from db.models import ReplayBase, Game, Action
from db.session import ReplaySession
from defs import Action as ActionCodes
from game_config import config

TIME_FORMAT = '%b %d %Y %I:%M:%S.%f'


class DbReplay(object):
    """ Contains helpers for replay DB.
    """
    def __init__(self):
        self.session = ReplaySession()
        self.current_game_id = None

    def reset_db(self):
        """ Re-applies DB schema.
        """
        ReplayBase.metadata.drop_all()
        ReplayBase.metadata.create_all()

    def add_game(self, name, map_name, date=None):
        """ Creates new Game in DB.
        """
        _date = datetime.now() if date is None else date
        new_game = Game(name=name, date=_date, map_name=map_name)
        self.session.add(new_game)
        self.session.commit()  # Commit to get game's id.
        self.current_game_id = new_game.id
        return self.current_game_id

    def add_action(self, action, message, game_id=None, date=None, with_commit=True):
        """ Creates new Action in DB.
        """
        _date = datetime.now() if date is None else date
        _game_id = self.current_game_id if game_id is None else game_id
        new_action = Action(game_id=_game_id, code=action, message=message, date=_date)
        self.session.add(new_action)
        if with_commit:  # What is the purpose of with_commit arg?
            self.session.commit()

    def get_all_games(self):
        """ Retrieves all games with their length.
        """
        games = []
        rows = self.session.query(Game, func.count(Action.id)).outerjoin(
            Action, and_(Game.id == Action.game_id, Action.code == ActionCodes.TURN)).group_by(
            Game.id).order_by(Game.id).all()
        for row in rows:
            game_data, game_length = row
            game = {
                'idx': game_data.id,
                'name': game_data.name,
                'date': game_data.date.strftime(TIME_FORMAT),
                'map': game_data.map_name,
                'length': game_length,
            }
            games.append(game)
        return games

    def get_all_actions(self, game_id):
        """ Retrieves all actions for the game.
        """
        actions = []
        rows = self.session.query(Action).filter(Action.game_id == game_id).order_by(Action.id).all()
        for row in rows:
            action = {
                'code': row.code,
                'message': row.message,
                'date': row.date.strftime(TIME_FORMAT),
            }
            actions.append(action)
        return actions

    def close(self):
        """ Closes and commits session.
        """
        self.session.commit()
        self.session.close()

    def commit(self):
        """ Makes commit to DB.
        """
        self.session.commit()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()


def generate_replay01(db):
    db.add_game('Test', config.MAP_NAME)
    db.add_action(ActionCodes.LOGIN, '{"name": "TestPlayer"}')
    db.add_action(ActionCodes.MOVE, '{"line_idx": 1, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 2, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # in point 2
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 3, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # in point 3
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 4, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 4
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 5, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 5
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 6, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 6
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 7, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 7
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 8, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 8
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 9, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 9
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 19, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 10
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 38, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 20
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 57, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 30
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 76, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 40
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 95, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 50
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 114, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 60
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 133, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 70
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 152, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 80
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 171, "speed": 1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 90
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)  # point 100
    db.add_action(ActionCodes.MOVE, '{"line_idx": 180, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 179, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 99
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 178, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 98
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 177, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 97
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 176, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 96
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 175, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 95
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 174, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 94
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 173, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 93
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 172, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 92
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 162, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 91
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 143, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 81
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 124, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 71
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 105, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 61
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 86, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 51
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 67, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 41
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 48, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 31
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 29, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 21
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.MOVE, '{"line_idx": 10, "speed": -1, "train_idx": 1}')
    db.add_action(ActionCodes.TURN, None)  # point 11
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)
    db.add_action(ActionCodes.TURN, None)  # point 1


REPLAY_GENERATORS = {
    'replay01': generate_replay01,
}


@task
def generate_replay(ctx, replay_name=None):
    """ Generates 'replay.db'.
    """
    with DbReplay() as db:
        if replay_name is not None and replay_name not in REPLAY_GENERATORS:
            print("Error, unknown replay name: '{}', available: {}".format(
                replay_name, ', '.join(REPLAY_GENERATORS.keys())))
            sys.exit(1)
        db.reset_db()
        replays_to_generate = REPLAY_GENERATORS.keys() if replay_name is None else [replay_name, ]
        for curr_replay in replays_to_generate:
            replay_generator = REPLAY_GENERATORS[curr_replay]
            replay_generator(db)
            print("Replay '{}' has been generated.".format(curr_replay))
        sys.exit(0)
