""" Game entity
"""
from entity.Map import Map
from log import LOG

# all registered games
game_map = {}

class Game(object):
    """ game
        has:
          players - list of players on this game
          map - game map
          status - [ready, run, finish]
          tick_time - current time
          max_tick_time - time of game session
          name - unique game name
          ...

    """
    def __init__(self, name):
        self._players = list()
        self.map = Map('map01')
        self.name = name
        LOG(LOG.INFO, "Create game: %s", self.name)


    @staticmethod
    def create(name):
        game = None
        if name in game_map.keys():
            game = game_map[name]
        else:
            game = Game(name)
            game_map[name] = game
        return game


    def add_player(self, player):
        if not player in self._players:
            LOG(LOG.INFO, "Game: Add player [%s]", player.name)
            self._players.append(player)

