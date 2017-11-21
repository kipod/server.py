import sqlite3
import os
from datetime import datetime
DEF_PATH_DB = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'replay.db')

TIME_FORMAT = '%b %d %Y %I:%M:%S.%f'

class DbReplay(object):
    """
    DB map generator
    """
    def __init__(self, db_path=DEF_PATH_DB):
        self._connection = sqlite3.connect(db_path)


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
        if date is None:
            date = datetime.now().strftime(TIME_FORMAT)
        self._connection.execute('insert into game (name, date, map) values (?, ?, ?)',
                                 (name, date, map_name))
        self._connection.commit()
        cursor = self._connection.execute('select max(id) from game')
        self._current_game_id = int(cursor.fetchone()[0])
        return self._current_game_id

    def add_action(self, action, message, game_id=None, date=None, with_commit=True):
        if date is None:
            date=datetime.now().strftime(TIME_FORMAT)
        if game_id is None:
            game_id = self._current_game_id
        self._connection.execute('insert into action \
                                  (game_id, code, message, date)\
                                  values (?, ?, ?, ?)',
                                 (game_id, action, message, date))
        if with_commit:
            self._connection.commit()
        #cursor = self._connection.execute('select max(id) from action')
        #return int(cursor.fetchone()[0])

    def commit(self):
        """ commit to db """
        if self._connection:
            self._connection.commit()

    def __enter__(self):
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        self.close()


    def close(self):
        self._connection.close()


def main():
    with DbReplay() as db:
        db.reset_db()
        db.add_game('Test', 'map01')


if __name__ == '__main__':
    main()
