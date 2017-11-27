import sqlite3
import os
from datetime import datetime
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
DEF_PATH_DB = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'replay.db')
from defs import Action
from log import LOG

TIME_FORMAT = '%b %d %Y %I:%M:%S.%f'

class DbReplay(object):
    """
    DB map generator
    """
    def __init__(self, db_path=DEF_PATH_DB):
        self._connection = sqlite3.connect(db_path)
        self._current_game_id = 0
        self.post_queries = []

    def drop_table(self, table):
        """ drop table by name with ignore error
        """
        try:
            self._connection.execute('drop table {}'.format(table))
            self._connection.commit()
        except sqlite3.Error:
            pass

    def reset_db(self):
        """ apply DB schema
        """
        self.drop_table('game')
        self.drop_table('action')

        sql_set = (
            'create table game (id integer primary key, name text,\
                                date text, map text)',
            'create table action (id integer primary key, game_id integer,\
                                    code integer, message text, date text)',
        )

        for sql in sql_set:
            self._connection.execute(sql)
        self._connection.commit()

    def max_game_id(self):
        cursor = self._connection.execute('select max(id) from game')
        return int(cursor.fetchall()[0])

    def add_game(self, name, map_name, date=None):
        try:
            if date is None:
                date = datetime.now().strftime(TIME_FORMAT)
            self._connection.execute('insert into game (name, date, map) values (?, ?, ?)',
                                    (name, date, map_name))
            self._connection.commit()
            cursor = self._connection.execute('select max(id) from game')
            self._current_game_id = int(cursor.fetchone()[0])
            return self._current_game_id
        except sqlite3.Error as error:
            LOG(LOG.ERROR, "Cannot write game: %s into replay.db", name)
            LOG(LOG.ERROR, "Error: %s", error.args[0])
            return None

    def add_action(self, action, message, game_id=None, date=None, with_commit=True):
        try:
            if date is None:
                date = datetime.now().strftime(TIME_FORMAT)
            if game_id is None:
                game_id = self._current_game_id
            sql = {"sql": 'insert into action \
                                     (game_id, code, message, date)\
                                     values (?, ?, ?, ?)',
                   "args": (game_id, action, message, date)
                  }
            if with_commit:
                self._connection.execute(sql['sql'], sql['args'])
                self._connection.commit()
            else:
                self.post_queries.append(sql)

        except sqlite3.Error as error:
            LOG(LOG.ERROR, "Cannot write action: %d into replay.db", action)
            LOG(LOG.ERROR, "Error: %s", error.args[0])

    def commit(self):
        """ commit to db """
        if self._connection:
            self._connection.commit()

    def get_all_games(self):
        """ retrieve all games """
        games = []
        cur = self._connection.cursor()
        cur.execute('select id, name, date, map from game order by id')
        for row in cur.fetchall():
            cur.execute('select count(id) from action where action.game_id=? and action.code=5',
                        (row[0], ))
            game_length = cur.fetchone()[0]
            game = {
                'idx': row[0],
                'name': row[1],
                'date': row[2],
                'map': row[3],
                'length': game_length
            }
            games.append(game)
        return games

    def get_all_actions(self, game_id):
        """ retrieve all actions for the game """
        actions = []
        cur = self._connection.cursor()
        cur.execute('select code, message, date from action where game_id=? order by id',
                    (game_id,))
        for row in cur.fetchall():
            action = {
                'code': row[0],
                'message': row[1],
                'date': row[2]
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
                self._connection.execute(sql['sql'], sql['args'])
            self._connection.commit()
        except sqlite3.Error as error:
            LOG(LOG.ERROR, "Cannot execute post queries in replay.db")
            LOG(LOG.ERROR, "Error: %s", error.args[0])
        self._connection.close()


def main():
    with DbReplay() as db:
        db.reset_db()
        db.add_game('Test', 'map02')
        db.add_action(Action.MOVE, "{" +
                      '\n  "line_idx": 1,' +
                      '\n  "speed": 1,' +
                      '\n  "train_idx": 0' +
                      '\n}')
        db.add_action(Action.TURN, None)


if __name__ == '__main__':
    main()
