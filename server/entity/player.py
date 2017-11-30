""" Entity Player.
"""
import json
import uuid

from entity.map import Map
from entity.point import Point
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
        self.train = []
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
        self.train.append(train)

    def set_home(self, point: Point, level: Map):
        """ Sets home point.
        """
        self.home = point
        self.town = level.post[point.post_id]

    def from_json_str(self, string_data):
        data = json.loads(string_data)
        self.idx = data['idx']
        self.name = data['name']
