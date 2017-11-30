""" Game map entity.
"""
import json
import os
import sqlite3

from entity.Line import Line
from entity.Point import Point
from entity.Post import Post
from entity.Serializable import Serializable
from logger import log

PATH_MAP_DB = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'db', 'map.db')


class Map(Serializable):
    """ Map of game space.
    """
    def __init__(self, name=None):
        self.okey = False
        self.train = []
        if name is None:
            return  # Empty map.
        try:
            self.name = name

            connection = sqlite3.connect(PATH_MAP_DB)
            cur = connection.cursor()

            cur.execute(
                """SELECT id, size_x, size_y
                   FROM map
                   WHERE name=?""",
                (self.name, )
            )
            row = cur.fetchone()
            self.idx = row[0]
            self.size = (row[1], row[2])

            self.line = {}
            cur.execute(
                """SELECT id, len, p0, p1
                   FROM line
                   WHERE map_id=?
                   ORDER BY id""",
                (self.idx,)
            )
            for row in cur.fetchall():
                self.line[row[0]] = Line(row[0], row[1], row[2], row[3])

            self.point = {}
            self.coordinate = {}
            cur.execute(
                """SELECT id, post_id, x, y
                   FROM point
                   WHERE map_id=?
                   ORDER BY id""",
                (self.idx,)
            )
            for row in cur.fetchall():
                post_id = row[1]
                self.coordinate[row[0]] = {'idx': row[0], 'x': row[2], 'y': row[3]}
                if post_id == 0:
                    self.point[row[0]] = Point(row[0])
                else:
                    self.point[row[0]] = Point(row[0], post_id=post_id if post_id != 0 else None)

            self.post = {}
            cur.execute(
                """SELECT id, name, type, population, armor, product
                   FROM post
                   WHERE map_id=?
                   ORDER BY id""",
                (self.idx,)
            )
            for row in cur.fetchall():
                self.post[row[0]] = Post(
                    idx=row[0], name=row[1], post_type=row[2], population=row[3], armor=row[4], product=row[5])

            connection.close()
            self.okey = True

        except sqlite3.Error as exception:
            log(log.Error, "An error occurred: {}".format(exception.args[0]))

    def add_train(self, train):
        self.train.append(train)

    def from_json_str(self, string_data):
        data = json.loads(string_data)
        self.idx = data['idx']
        self.name = data['name']

        self.line = {}
        for line in data['line']:
            self.line[line['idx']] = Line(line['idx'], line['length'], line['point'][0], line['point'][1])

        self.point = {}
        for p in data['point']:
            self.point[p['idx']] = Point(p['idx'], post_id=p[u'post_id'] if 'post_id' in p else None)

        self.okey = True

    def layer_to_json_str(self, layer):
        data = {}
        choice_list = ()
        if layer == 0:
            choice_list = ('idx', 'name', 'point', 'line')
        elif layer == 1:
            choice_list = ('idx', 'post', 'train')
        elif layer == 10:
            choice_list = ('idx', 'size', 'coordinate')
        for key in self.__dict__:
            if key in choice_list:
                attribute = self.__dict__[key]
                if isinstance(attribute, dict):
                    data[key] = [i for i in attribute.values()]
                else:
                    data[key] = attribute
        return json.dumps(data, default=lambda o: o.__dict__, sort_keys=True, indent=4)
