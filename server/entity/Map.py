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
        if name is None:
            return # empty map
        try:
            connection = sqlite3.connect(PATH_MAP_DB)
            cur = connection.cursor()
            cur.execute('select id from map where name=?', (name, ))
            self.idx = cur.fetchone()[0]
            self.name = name
            self.line = []
            cur.execute('select id, len, p0, p1'
                        ' from line'
                        ' where map_id=?'
                        ' order by id', (self.idx,))
            for row in cur.fetchall():
                self.line.append(Line(row[0], row[1], row[2], row[3]))
            self.point = []
            cur.execute('select id, post_id'
                        ' from point'
                        ' where map_id=?'
                        ' order by id', (self.idx,))
            for row in cur.fetchall():
                post_id = row[1]
                if post_id == 0:
                    self.point.append(Point(row[0]))
                else:
                    self.point.append(Point(row[0], post_id=post_id))

            self.post = []
            cur.execute('select id, name, type, population, armor, product'
                        ' from post'
                        ' where map_id=?'
                        ' order by id', (self.idx,))
            for row in cur.fetchall():
                self.post.append(Post(
                    idx=row[0],
                    name=row[1],
                    post_type=row[2],
                    population=row[3],
                    armor=row[4],
                    product=row[5]))

            connection.close()
            self.okey = True
        except sqlite3.Error as exception:
            LOG(LOG.Error, "An error occurred: %s", exception.args[0])


    def from_json_str(self, string_data):
        data = json.loads(string_data)
        self.idx = data[u"idx"]
        self.name = data[u"name"]
        lines = data[u"line"]
        self.line = []
        for line in lines:
            self.line.append(Line(line[u"idx"],
                                  line[u"length"],
                                  line[u"point"][0],
                                  line[u"point"][1]))
        self.point = []
        points = data[u"point"]
        for p in points:
            if u"post_id" in p.keys():
                self.point.append(Point(p[u"idx"],
                                        post_id=p[u"post_id"]))
            else:
                self.point.append(Point(p[u"idx"]))
        self.okey = True

    def layer_to_json_str(self, layer):
        data = {}
        choise_list = ()
        if layer == 0:
            choise_list = ('idx', 'name', 'point', 'line')
        elif layer == 1:
            choise_list = ('idx', 'post')
        for key in self.__dict__.keys():
            if key in choise_list:
                data[key] = self.__dict__[key]
        return json.dumps(data, default=lambda o: o.__dict__, sort_keys=True, indent=4)
