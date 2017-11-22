"""
Observer Entity. Creates when to server connects Observer-Client for watch replay(s)
"""
from db.replay import DbReplay
from defs import Action, Result
from log import LOG
from entity.Game import Game
from entity.Player import Player
import json


class Observer(object):
    """ Observer entity """
    PLAYER_NAME = '-=Observer=-'

    def __init__(self):
        self._db = DbReplay()
        self._games = self._db.get_all_games()
        self._game = None
        self._actions = []
        self._map_name = None
        self._game_name = None
        self._current_turn = 0
        self._current_action = 0
        self._max_turn = 0

    def games(self):
        """ retrive list of games """
        return self._games

    def reset_game(self):
        """ reset the game to init state """
        self._game = Game(self._game_name, self._map_name, observed=True)
        self._game.add_player(Player(Observer.PLAYER_NAME))
        self._current_turn = 0
        self._current_action = 0

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
                return Result.OKEY, self._game.map.layer_to_json_str(layer)
            else:
                return Result.RESOURCE_NOT_FOUND, None
        return Result.BAD_COMMAND, None

    def game_turn(self, turns):
        """ play game turns """
        assert turns > 0
        sub_turn = 0
        for action in self._actions[self._current_action:]:
            self._current_action += 1
            if action['code'] == Action.MOVE:
                data = json.loads(action['message'])
                self._game.move_train(data['train_idx'],
                                      data['speed'],
                                      data['line_idx'])
            elif action['code'] == Action.TURN:
                self._game.tick()
                sub_turn += 1
                self._current_turn += 1
            if sub_turn >= turns:
                break

    def _on_turn(self, data):
        if self._game is None:
            return Result.BAD_COMMAND, None
        if not self._actions:
            return Result.RESOURCE_NOT_FOUND, None
        if 'idx' not in data:
            return Result.BAD_COMMAND, None
        turn = data['idx']
        if turn < 0:
            turn = 0
        elif turn > self._max_turn:
            turn = self._max_turn

        if turn == self._current_turn:
            return Action.OKEY, None
        delta_turn = turn - self._current_turn
        if delta_turn > 0:
            self.game_turn(delta_turn)
        elif delta_turn < 0:
            self.reset_game()
            if turn > 0:
                self.game_turn(turn)
        self._current_turn = turn
        return Result.OKEY, None

    def _on_game(self, data):
        if 'idx' not in data:
            return Result.BAD_COMMAND, None
        self._game = None
        game_id = data['idx']
        for game in self._games:
            game_name = game['name']
            if game['idx'] == game_id:
                self._game_name = game_name
                self._map_name = game['map']
                self.reset_game()
                LOG(LOG.INFO, "Observer selected game: %s", game_name)
                self._actions = self._db.get_all_actions(game_id)
                self._max_turn = game['length']
                break
        if self._game is None:
            return Result.RESOURCE_NOT_FOUND, None
        return Result.OKEY, None

    COMMAND_MAP = {
        Action.MAP : _on_get_map,
        Action.TURN : _on_turn,
        Action.GAME : _on_game
    }
