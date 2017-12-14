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

    @staticmethod
    def reset_db():
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

    # pylint: disable=R0913
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


def generate_replay01(database: DbReplay):
    """ Generates test game replay.
    """
    database.add_game('Test', config.MAP_NAME)
    database.add_action(ActionCodes.LOGIN, '{"name": "TestPlayer"}')

    def insert_replay_move_and_turns(database: DbReplay, line_idx: int, speed: int, train_idx: int, turns_count: int):
        """ Inserts into replays database MOVE action + number of TURN actions.
        """
        database.add_action(
            ActionCodes.MOVE,
            '{{"line_idx": {0}, "speed": {1}, "train_idx": {2}}}'.format(line_idx, speed, train_idx)
        )
        for _ in range(turns_count):
            database.add_action(ActionCodes.TURN, None)

    def forward_move(line_idx: int, count_turns: int):
        """ Forward move. Inner helper to simplify records formatting.
        """
        insert_replay_move_and_turns(database, line_idx, 1, 1, count_turns)

    def reverse_move(line_idx: int, count_turns: int):
        """ Reverse move. Inner helper to simplify records formatting.
        """
        insert_replay_move_and_turns(database, line_idx, -1, 1, count_turns)

    forward = [
        (1, 3), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4), (8, 4), (9, 4),
        (19, 5), (38, 5), (57, 5), (76, 5), (95, 5), (114, 5), (133, 5), (152, 5), (171, 6)
    ]
    for move in forward:
        forward_move(*move)

    reverse = [
        (180, 3), (179, 4), (178, 4), (177, 4), (176, 4), (175, 4), (174, 4), (173, 4), (172, 4),
        (162, 5), (143, 5), (124, 5), (105, 5), (86, 5), (67, 5), (48, 5), (29, 5), (10, 6)
    ]
    for move in reverse:
        reverse_move(*move)


REPLAY_GENERATORS = {
    'replay01': generate_replay01,
}


@task
def generate_replay(_, replay_name=None):
    """ Generates 'replay.db'.
    """
    with DbReplay() as database:
        if replay_name is not None and replay_name not in REPLAY_GENERATORS:
            print("Error, unknown replay name: '{}', available: {}".format(
                replay_name, ', '.join(REPLAY_GENERATORS.keys())))
            sys.exit(1)
        database.reset_db()
        replays_to_generate = REPLAY_GENERATORS.keys() if replay_name is None else [replay_name, ]
        for current_replay in replays_to_generate:
            replay_generator = REPLAY_GENERATORS[current_replay]
            replay_generator(database)
            print("Replay '{}' has been generated.".format(current_replay))
        sys.exit(0)
