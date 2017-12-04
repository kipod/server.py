""" Entity Player.
"""
import json
import uuid

from entity.point import Point
from entity.post import Post
from entity.serializable import Serializable


class Player(Serializable):
    """ Player
    * name - player name
    * id - player id
    * train - list of trains
    * home - point of the home town
    """

    # All indexes of registered players
    PLAYERS = {}

    def __init__(self, name):
        self.name = name
        self.idx = None
        self.train = {}
        self.home = None
        self.town = None

        if name in Player.PLAYERS:
            self.idx = Player.PLAYERS[name]
        else:
            Player.PLAYERS[name] = self.idx = str(uuid.uuid4())

    def __eq__(self, other):
        return self.idx == other.idx

    def add_train(self, train):
        """ Adds train to the player.
        """
        train.player_id = self.idx
        self.train[train.idx] = train

    def set_home(self, point: Point, post: Post):
        """ Sets home point.
        """
        post.player_id = self.idx
        self.home = point
        self.town = post

    def from_json_str(self, string_data):
        data = json.loads(string_data)
        self.idx = data['idx']
        self.name = data['name']

    def to_json_str(self):
        data = {}
        for key in self.__dict__:
            attribute = self.__dict__[key]
            if isinstance(attribute, dict):
                data[key] = [i for i in attribute.values()]
            else:
                data[key] = attribute
        return json.dumps(data, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def __str__(self):
        return "<Player(idx={}, name='{}', home_point_idx={}, town_post_idx={}, trains_idx=[{}])>".format(
            self.idx, self.name, self.home.idx, self.town.idx, ', '.join([str(idx) for idx in self.train])
        )
