""" Entity Player.
"""
import json
import uuid

from game_config import config
from entity.point import Point
from entity.post import Post
from entity.train import Train


class Player(object):
    """ Player
    * name - player name
    * id - player id
    * train - list of trains
    * home - point of the home town
    """

    # All indexes of registered players.
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
        """ loads object from json string
        """
        data = json.loads(string_data)
        if data.get('idx'):
            self.idx = data['idx']
        if data.get('name'):
            self.name = data['name']
        if data.get('train'):
            self.train = {
                t['idx']: Train(
                    t['idx'], line_idx=t['line_idx'], position=t['position'], speed=t['speed'],
                    player_id=t['player_id'], level=t['level'], goods=t['goods'], post_type=t['post_type']
                )
                for t in data['train']
            }
        if data.get('home'):
            home = data['home']
            self.home = Point(home['idx'], home['post_id'])
        if data.get('town'):
            town = data['town']
            self.town = Post(
                town['idx'], town['name'], town['type'], population=town['population'], armor=town['armor'],
                product=town['product'], level=town['level'], player_id=town['player_id'], point_id=town['point_id']
            )

    def to_json_str(self):
        """ store object to JSON string
        """
        data = {}
        for key in self.__dict__:
            attribute = self.__dict__[key]
            if isinstance(attribute, dict):
                data[key] = [i for i in attribute.values()]
            else:
                data[key] = attribute
        return json.dumps(data, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def __repr__(self):
        return "<Player(idx={}, name='{}', home_point_idx={}, town_post_idx={}, trains_idx=[{}])>".format(
            self.idx, self.name, self.home.idx, self.town.idx, ', '.join([str(idx) for idx in self.train])
        )

    @property
    def rating(self):
        """ calculate player's rating
        """
        rating_value = self.town.population * 1000
        rating_value += (self.town.product + self.town.armor)
        sum_next_level_price = 0
        for train in self.train.values():
            for level in range(1, train.level):
                sum_next_level_price += config.TRAIN_LEVELS[level]['next_level_price']
        for level in range(1, self.town.level):
            sum_next_level_price += config.TOWN_LEVELS[level]['next_level_price']
        rating_value += sum_next_level_price

        return rating_value
