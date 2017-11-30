import os
import sqlite3
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from defs import Action
from logger import log

DEF_PATH_DB = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'replay.db')
TIME_FORMAT = '%b %d %Y %I:%M:%S.%f'


class DbReplay(object):
    """ DB map generator.
    """
    def __init__(self, db_path=DEF_PATH_DB):
        self._connection = sqlite3.connect(db_path)
        self._current_game_id = 0
        self.post_queries = []

    def drop_table(self, table):
        """ Drops table by name with ignore error.
        """
        try:
            self._connection.execute("DROP TABLE {}".format(table))
            self._connection.commit()
        except sqlite3.Error:
            pass

    def reset_db(self):
        """ Applies DB schema.
        """
        self.drop_table('game')
        self.drop_table('action')

        sql_set = (
            """CREATE TABLE game
               (id integer primary key, name text, date text, map text)""",
            """CREATE TABLE action
               (id integer primary key, game_id integer, code integer, message text, date text)""",
        )

        for sql in sql_set:
            self._connection.execute(sql)
        self._connection.commit()

    def max_game_id(self):
        cursor = self._connection.execute("SELECT max(id) FROM game")
        return int(cursor.fetchone()[0])

    def add_game(self, name, map_name, date=None):
        try:
            if date is None:
                date = datetime.now().strftime(TIME_FORMAT)
            self._connection.execute(
                """INSERT INTO game (name, date, map)
                   VALUES (?, ?, ?)""",
                (name, date, map_name)
            )
            self._connection.commit()
            self._current_game_id = self.max_game_id()
            return self._current_game_id
        except sqlite3.Error as error:
            log(log.ERROR, "Cannot write game: {} into replay.db".format(name))
            log(log.ERROR, "Error: {}".format(error.args[0]))
            return None

    def add_action(self, action, message, game_id=None, date=None, with_commit=True):
        try:
            if date is None:
                date = datetime.now().strftime(TIME_FORMAT)
            if game_id is None:
                game_id = self._current_game_id
            sql = (
                """INSERT INTO action (game_id, code, message, date)
                   VALUES (?, ?, ?, ?)""",
                (game_id, action, message, date)
            )
            if with_commit:
                self._connection.execute(*sql)
                self._connection.commit()
            else:
                self.post_queries.append(sql)

        except sqlite3.Error as error:
            log(log.ERROR, "Cannot write action: {} into replay.db".format(action))
            log(log.ERROR, "Error: {}".format(error.args[0]))

    def commit(self):
        """ Commits to db.
        """
        if self._connection:
            self._connection.commit()

    def get_all_games(self):
        """ Retrieves all games.
        """
        games = []
        cur = self._connection.cursor()
        cur.execute("""SELECT id, name, date, map
                       FROM game
                       ORDER BY id""")
        for row in cur.fetchall():
            cur.execute(
                """SELECT count(id)
                   FROM action
                   WHERE action.game_id=?
                   AND action.code=?""",
                (row[0], Action.TURN)
            )
            game_length = cur.fetchone()[0]
            game = {
                'idx': row[0],
                'name': row[1],
                'date': row[2],
                'map': row[3],
                'length': game_length,
            }
            games.append(game)
        return games

    def get_all_actions(self, game_id):
        """ Retrieves all actions for the game.
        """
        actions = []
        cur = self._connection.cursor()
        cur.execute(
            """SELECT code, message, date
               FROM action
               WHERE game_id=?
               ORDER BY id""",
            (game_id,)
        )
        for row in cur.fetchall():
            action = {
                'code': row[0],
                'message': row[1],
                'date': row[2],
            }
            actions.append(action)
        return actions

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def close(self):
        try:
            for sql in self.post_queries:
                self._connection.execute(*sql)
            self._connection.commit()
        except sqlite3.Error as error:
            log(log.ERROR, "Cannot execute post queries in replay.db")
            log(log.ERROR, "Error: {}".format(error.args[0]))
        self._connection.close()


def main():
    with DbReplay() as db:
        db.reset_db()
        db.add_game('Test', 'map02')
        db.add_action(Action.MOVE, '{"line_idx": 13, "speed": 1, "train_idx": 0}')
        db.add_action(Action.TURN, None)
        db.add_action(Action.MOVE, '{"line_idx": 14, "speed": 1, "train_idx": 0}')
        db.add_action(Action.TURN, None)
        db.add_action(Action.TURN, None)
        db.add_action(Action.MOVE, '{"line_idx": 15, "speed": 1, "train_idx": 0}')
        db.add_action(Action.TURN, None)
        db.add_action(Action.MOVE, '{"line_idx": 16, "speed": 1, "train_idx": 0}')
        db.add_action(Action.TURN, None)
        db.add_action(Action.TURN, None)
        db.add_action(Action.MOVE, '{"line_idx": 17, "speed": 1, "train_idx": 0}')
        db.add_action(Action.TURN, None)
        db.add_action(Action.TURN, None)
        db.add_action(Action.TURN, None)
        db.add_action(Action.MOVE, '{"line_idx": 18, "speed": 1, "train_idx": 0}')
        db.add_action(Action.TURN, None)
        db.add_action(Action.TURN, None)
        db.add_action(Action.TURN, None)


if __name__ == '__main__':
    main()
