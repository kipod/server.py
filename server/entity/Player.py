"""
Entity Player
"""
import uuid
import json
from .Serializable import Serializable

# all registered players
PLAYER_LIST = list()

class Player(Serializable):
    """
    Player
    * name - player name
    * id - player id
    * trains - list of trains
    * home - point of the home town
    """
    def __init__(self, name):
        self.name = name
        self.idx = None
        for player in PLAYER_LIST:
            if player.name == name:
                self.idx = player.idx
                break
        if not self.idx:
            self.idx = str(uuid.uuid4())
            PLAYER_LIST.append(self)
        self.train = []
        self.home = None

    def __eq__(self, other):
        return self.idx == other.idx

    def add_train(self, train):
        """ add train to the player """
        train.player_id = self.idx
        self.train.append(train)

    def set_home(self, point):
        """ set home point """
        self.home = point

    def from_json_str(self, string_data):
        data = json.loads(string_data)
        self.idx = data["idx"]
        self.name = data["name"]
