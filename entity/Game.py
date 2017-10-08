""" Game entity
"""
from entity.Map import Map

class Game(object):
    """ game
        has:
          sessions - list of network sessions
          map - game map
          status - [ready, run, finish]
          tick_time - current time
          max_tick_time - time of game session
          ...

    """
    def __init__(self):
        self.sessions = list()
        self.map = Map()
