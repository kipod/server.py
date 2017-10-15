"""
Entity Player
"""
import uuid
from .Serializable import Serializable
import json

# all registred players
player_list = list()

class Player(Serializable):
    """
    Player
    """
    def __init__(self, name):
        self.name = name
        self.id = None
        for player in player_list:
            if player.name == name:
                self.id = player.id
                break
        if not self.id:
            self.id = str(uuid.uuid4())
            player_list.append(self)

    def from_json_str(self, string_data):
        data = json.loads(string_data)
        self.id = data[u"id"]
        self.name = data[u"name"]
	