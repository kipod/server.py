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
                                date text)',
            'create table action (id integer primary key, game_id integer,\
                                    code integer, message text, date text)',
        )

        for sql in sql_set:
            self._connection.execute(sql)
        self._connection.commit()

    def max_game_id(self):
        cursor = self._connection.execute('select max(id) from game')
        return int(cursor.fetchall()[0])

    def add_game(self, name, date=None):
        if date is None:
            date=datetime.now().strftime(TIME_FORMAT)
        self._connection.execute('insert into game (name, date) values (?, ?)',
                                 (name, date))
        self._connection.commit()
        cursor = self._connection.execute('select max(id) from game')
        self._current_game_id = int(cursor.fetchone()[0])
        return self._current_game_id

    async def add_game_async(self, name):
        return await self.add_game(name)

    def add_action(self, action, message, game_id=None, date=None):
        if date is None:
            date=datetime.now().strftime(TIME_FORMAT)
        if game_id is None:
            game_id = self._current_game_id
        self._connection.execute('insert into action \
                                  (game_id, code, message, date)\
                                  values (?, ?, ?, ?)',
                                 (game_id, action, message, date))
        self._connection.commit()
        #cursor = self._connection.execute('select max(id) from action')
        #return int(cursor.fetchone()[0])

    async def add_action_async(self, action, message):
        return await self.add_action(action, message)

    def __enter__(self):
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        self.close()


    def close(self):
        self._connection.close()


def main():
    with DbReplay() as db:
        db.reset_db()
        game_id = db.add_game('Test')


if __name__ == '__main__':
    main()
