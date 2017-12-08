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

def insert_replay_move_and_turns(database, line_idx: int, speed: int, train_idx: int, turns_count: int):
    """ Inserts into replays database MOVE action + number of TURN actions
    """
    database.add_action(ActionCodes.MOVE,
                        "{{\"line_idx\": {0}, \"speed\": {1}, \"train_idx\": {2}}}".format(line_idx, speed, train_idx))
    for _ in range(turns_count):
        database.add_action(ActionCodes.TURN, None)

def generate_replay01(database):
    """ Generate test game record
    """
    database.add_game('Test', config.MAP_NAME)
    database.add_action(ActionCodes.LOGIN, '{"name": "TestPlayer"}')

    def fwd(line_idx: int, count_turns: int):
        """ Forward move. Inner helper for simplify formatin records
        """
        insert_replay_move_and_turns(database, line_idx, 1, 1, count_turns)

    def rev(line_idx: int, count_turns: int):
        """ Reverse move. Inner helper for simplify formatin records
        """
        insert_replay_move_and_turns(database, line_idx, -1, 1, count_turns)

    # pylint: disable=C0321
    fwd(1, 3); fwd(2, 4); fwd(3, 4); fwd(4, 4); fwd(5, 4); fwd(6, 4); fwd(7, 4); fwd(8, 4); fwd(9, 4)
    fwd(19, 5); fwd(38, 5); fwd(57, 5); fwd(76, 5); fwd(95, 5); fwd(114, 5); fwd(133, 5); fwd(152, 5); fwd(171, 6)
    rev(180, 3); rev(179, 4); rev(178, 4); rev(177, 4); rev(176, 4); rev(175, 4); rev(174, 4); rev(173, 4); rev(172, 4)
    rev(162, 5); rev(143, 5); rev(124, 5); rev(105, 5); rev(86, 5); rev(67, 5); rev(48, 5); rev(29, 5); rev(10, 6)


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
