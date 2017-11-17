import sqlite3
import os
DEF_PATH_DB = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'replay.db')

class DbMap(object):
    """
    DB map generator
    """
    def __init__(self, db_path=DEF_PATH_DB):
        self._connection = sqlite3.connect(db_path)
        self.reset_db()


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

        sqls = (
            'create table game (id integer primary key, name text)',
            'create table line (id integer primary key, len integer,\
                                p0 integer, p1 integer, map_id integer)',
            'create table point (id integer primary key, map_id integer,\
                                 post_id integer, x integer, y integer)',
            'create table post (id integer primary key, name text,\
                                type integer, population integer,\
                                armor integer, product integer,\
                                map_id integer)'
        )
        for sql in sqls:
            self._connection.execute(sql)
        self._connection.commit()

    def max_map_id(self):
        cursor = self._connection.execute('select max(id) from map')
        return int(cursor.fetchall()[0])

    def add_map(self, size_x, size_y, name=''):
        self._connection.execute('insert into map (name, size_x, size_y) values (?, ?, ?)', (name, size_x, size_y))
        self._connection.commit()
        cursor = self._connection.execute('select max(id) from map')
        self._current_map_id = int(cursor.fetchone()[0])
        return self._current_map_id


    def add_line(self, length, p0, p1, map_id=None):
        if map_id is None:
            map_id = self._current_map_id
        self._connection.execute('insert into line \
                                  (len, p0, p1, map_id)\
                                  values (?, ?, ?, ?)',
                                 (length, p0, p1, map_id))
        self._connection.commit()
        cursor = self._connection.execute('select max(id) from line')
        return int(cursor.fetchone()[0])


    def add_point(self, post_id=0, map_id=None, x=0, y=0):
        if map_id is None:
            map_id = self._current_map_id
        self._connection.execute('insert into point \
                                  (post_id, map_id, x, y) values (?, ?, ?, ?)',
                                 (post_id, map_id, x, y))
        self._connection.commit()
        cursor = self._connection.execute('select max(id) from point')
        return int(cursor.fetchone()[0])


    def add_post(self, name, type_p, population=0, armor=0, product=0, map_id=None):
        if map_id is None:
            map_id = self._current_map_id
        self._connection.execute('insert into post \
                                  (name, map_id, type, population, armor, product)\
                                  values (?, ?, ?, ?, ?, ?)',
                                 (name, map_id, type_p, population, armor, product))
        self._connection.commit()
        cursor = self._connection.execute('select max(id) from post')
        return int(cursor.fetchone()[0])


    def __enter__(self):
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        self.close()


    def close(self):
        self._connection.close()


with DbMap() as db:
    ######################################################
    ## Map01. See map01.png
    map_id = db.add_map(name='map01', size_x=330, size_y=248)
    post_id = db.add_post('town-one', 1, 10) # town, population=10
    p1 = db.add_point(post_id, x=75, y=16)
    p2 = db.add_point(x=250, y=16)
    p3 = db.add_point(x=312, y=120)
    p4 = db.add_point(x=250, y=220)
    p5 = db.add_point(x=100, y=220)
    p6 = db.add_point(x=10, y=120)
    post_id = db.add_post('market-one', 2, product=20) # market, product=20
    p7 = db.add_point(post_id, x=134, y=70)
    p8 = db.add_point(x=200, y=70)
    p9 = db.add_point(x=235, y=120)
    p10 = db.add_point(x=198, y=160)
    p11 = db.add_point(x=134, y=160)
    p12 = db.add_point(x=85, y=120)
    db.add_line(10, p1, p7) #1: 1-7
    db.add_line(10, p8, p2) #2: 8-2
    db.add_line(10, p9, p3) #3: 9-3
    db.add_line(10, p10, p4) #4: 10-4
    db.add_line(10, p11, p5) #5: 11-5
    db.add_line(10, p7, p8) #6: 12-6
    db.add_line(10, p7, p8) #7: 7-8
    db.add_line(10, p8, p9) #8: 8-9
    db.add_line(10, p9, p10) #9: 9-10
    db.add_line(10, p10, p11) #10: 10-11
    db.add_line(10, p11, p12) #11: 11-12
    db.add_line(10, p12, p7) #12: 12-7
    print('OK')
    ######################################################
