"""
Observer Entity. Creates when to server connects Observer-Client for watch replay(s)
"""
from db.replay import DbReplay
from defs import Action, Result
from log import LOG
from entity.Game import Game


class Observer(object):
    """ Observer entity """
    def __init__(self):
        self._db = DbReplay()
        self._games = self._db.get_all_games()
        self._game = None
        self._actions = None

    def games(self):
        """ retrive list of games """
        return self._games

    def action(self, action, data):
        """ interpret observer's actions """
        if action in self.COMMAND_MAP:
            method = self.COMMAND_MAP[action]
            return method(self, data)
        return Result.RESOURCE_NOT_FOUND, None

    def _on_get_map(self, data):
        if self._game is None:
            return Result.RESOURCE_NOT_FOUND, None
        if 'layer' in data:
            layer = data['layer']
            if layer in (0, 1, 10):
                LOG(LOG.INFO, "Load map layer=%d", layer)
                message = self._game.map.layer_to_json_str(layer)
                return Result.OKEY, message
            else:
                return Result.RESOURCE_NOT_FOUND, None
        else:
            return Result.BAD_COMMAND, None

    def _on_turn(self, data):
        if not self._actions:
            return Result.RESOURCE_NOT_FOUND, None
        return Result.OKEY, None

    def _on_game(self, data):
        if 'idx' not in data:
            return Result.BAD_COMMAND, None
        self._game = None
        for game in self._games:
            if game['idx'] == data['idx']:
                self._game = Game(game['name'], game['map'], observed=True)

    COMMAND_MAP = {
        Action.MAP : _on_get_map,
        Action.TURN : _on_turn,
        Action.GAME : _on_game
    }
