""" Game map entity
"""
import sqlite3
from .log import LOG
from .Line import Line
from .Point import Point
from .Post import Post
from .Serializable import Serializable
import json
import os
import copy
PATH_MAP_DB = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'db', 'map.db')

class Map(Serializable):
    """ Map of game space
    """
    def __init__(self, name=None):
        self.okey = False
        self.train = []
        if name is None:
            return # empty map
        try:
            connection = sqlite3.connect(PATH_MAP_DB)
            cur = connection.cursor()
            cur.execute('select id, size_x, size_y from map where name=?', (name, ))
            row = cur.fetchone()
            self.idx = row[0]
            self.size = (row[1], row[2])
            self.name = name
            self.line = {}
            cur.execute('select id, len, p0, p1'
                        ' from line'
                        ' where map_id=?'
                        ' order by id', (self.idx,))
            for row in cur.fetchall():
                self.line[row[0]] = Line(row[0], row[1], row[2], row[3])
            self.point = {}
            self.coordinate = {}
            cur.execute('select id, post_id, x, y'
                        ' from point'
                        ' where map_id=?'
                        ' order by id', (self.idx,))
            for row in cur.fetchall():
                post_id = row[1]
                self.coordinate[row[0]] = {'x':row[2], 'y':row[3]}
                if post_id == 0:
                    self.point[row[0]] = Point(row[0])
                else:
                    self.point[row[0]] = Point(row[0], post_id=post_id)

            self.post = {}
            cur.execute('select id, name, type, population, armor, product'
                        ' from post'
                        ' where map_id=?'
                        ' order by id', (self.idx,))
            for row in cur.fetchall():
                self.post[row[0]] = Post(
                    idx=row[0],
                    name=row[1],
                    post_type=row[2],
                    population=row[3],
                    armor=row[4],
                    product=row[5])
            connection.close()
            self.okey = True
        except sqlite3.Error as exception:
            LOG(LOG.Error, "An error occurred: %s", exception.args[0])


    def add_train(self, train):
        self.train.append(train)

    def from_json_str(self, string_data):
        data = json.loads(string_data)
        self.idx = data["idx"]
        self.name = data["name"]
        lines = data["line"]
        self.line = {}
        for line in lines:
            self.line[line["idx"]] = Line(line["idx"],
                                          line["length"],
                                          line["point"][0],
                                          line["point"][1])
        self.point = {}
        points = data["point"]
        for p in points:
            if "post_id" in p:
                self.point[p["idx"]] = Point(p["idx"],
                                             post_id=p[u"post_id"])
            else:
                self.point[p["idx"]] = Point(p["idx"])
        self.okey = True


    def layer_to_json_str(self, layer):
        data = {}
        choise_list = ()
        if layer == 0:
            choise_list = ('idx', 'name', 'point', 'line')
        elif layer == 1:
            choise_list = ('idx', 'post', 'train')
        elif layer == 10:
            choise_list = ('idx', 'size', 'coordinate')
        for key in self.__dict__.keys():
            if key in choise_list:
                attribute = self.__dict__[key]
                if isinstance(attribute, dict):
                    data[key] = [i for i in attribute.values()]
                else:
                    data[key] = attribute
        return json.dumps(data, default=lambda o: o.__dict__, sort_keys=True, indent=4)
