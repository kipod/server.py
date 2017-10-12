""" Game entity
"""
from entity.Map import Map

class Game(object):
    """ game
        has:
          plyers - list of players on this game
          map - game map
          status - [ready, run, finish]
          tick_time - current time
          max_tick_time - time of game session
          ...

    """
    def __init__(self):
        self._players = list()
        self.map = Map()
        

    def add_player(self, player):
        if not player in self._players:
            self._players.append(player)

