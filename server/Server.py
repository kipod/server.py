""" Game server.
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from defs import SERVER_ADDR, SERVER_PORT, Action, Result
from entity.Game import Game
from entity.Observer import Observer
from entity.Player import Player
from logger import log


class GameServerProtocol(asyncio.Protocol):
    def __init__(self):
        asyncio.Protocol.__init__(self)
        self._action = None
        self.message_len = None
        self.message = None
        self.data = None
        self._player = None
        self._game = None
        self._replay = None
        self._observer = None
        self.peername = None
        self.transport = None

    def connection_made(self, transport):
        self.peername = transport.get_extra_info('peername')
        log(log.INFO, "Connection from {}".format(self.peername))
        self.transport = transport

    def connection_lost(self, exc):
        log(log.WARNING, "Connection from {0} lost. Reason: {1}".format(self.peername, exc))

    def data_received(self, data):
        if self.data:
            data = self.data + data
            self.data = None
        if self._process_data(data):
            try:
                data = json.loads(self.message)
            except json.decoder.JSONDecodeError:
                self._write_response(Result.BAD_COMMAND)
            if not isinstance(data, dict):
                self._write_response(Result.BAD_COMMAND)
            if self._observer:
                self._write_response(*self._observer.action(self._action, data))
            else:
                log(log.INFO, Action(self._action))
                log(log.INFO, self.message)
                if self._action in self.COMMAND_MAP:
                    method = self.COMMAND_MAP[self._action]
                    method(self, data)
                    if self._replay and self._action in (Action.MOVE, ):
                        self._replay.add_action(self._action, self.message, with_commit=False)
                else:
                    self._write_respose(Result.BAD_COMMAND)
            self._action = None

    def _process_data(self, data):
        """ Parses input command.
        returns: True if command parsing completed
        """
        # Read action [4 bytes]:
        if not self._action:
            if len(data) < 4:
                self.data = data
                return False
            self._action = Action(int.from_bytes(data[0:4], byteorder='little'))
            self.message_len = 0
            data = data[4:]
            if self._action in (Action.LOGOUT, Action.OBSERVER):  # Commands without data.
                self.data = data
                self.message = '{}'
                return True
        # Read size of message:
        if not self.message_len:
            if len(data) < 4:
                self.data = data
                return False
            self.message_len = int.from_bytes(data[0:4], byteorder='little')
            data = data[4:]
        # Read message:
        if len(data) < self.message_len:
            self.data = data
            return False
        self.message = data[0:self.message_len].decode('utf-8')
        self.data = data[self.message_len:]
        return True

    def _write_response(self, result, message=None):
        resp_message = '' if message is None else message
        self.transport.write(result.to_bytes(4, byteorder='little'))
        self.transport.write(len(resp_message).to_bytes(4, byteorder='little'))
        self.transport.write(resp_message.encode('utf-8'))

    def _on_login(self, data: dict):
        if 'name' in data:
            game_name = 'Game of {}'.format(data['name'])
            self._game = Game.create(game_name)
            self._replay = self._game.replay
            self._player = Player(data['name'])
            self._game.add_player(self._player)
            log(log.INFO, "Login player: {}".format(data['name']))
            message = self._player.to_json_str()
            self._write_response(Result.OKEY, message)
        else:
            self._write_response(Result.BAD_COMMAND)

    def _on_logout(self, _):
        self._write_response(Result.OKEY)
        log(log.INFO, "Logout player: {}".format(self._player.name))
        self.transport.close()
        self._game.stop()
        del self._game
        self._game = None

    def _on_get_map(self, data: dict):
        if 'layer' in data:
            layer = data['layer']
            if layer in (0, 1, 10):
                log(log.INFO, "Load map layer={}".format(layer))
                message = self._game.map.layer_to_json_str(layer)
                self._write_response(Result.OKEY, message)
            else:
                self._write_response(Result.RESOURCE_NOT_FOUND)
        else:
            self._write_response(Result.BAD_COMMAND)

    def _on_move(self, data: dict):
        res = self._game.move_train(data['train_idx'], data['speed'], data['line_idx'])
        self._write_response(res)

    def _on_turn(self, _):
        self._game.turn()
        self._write_response(Result.OKEY)

    def _on_observer(self, _):
        if self._game or self._observer:
            self._write_response(Result.BAD_COMMAND)
        else:
            self._observer = Observer()
            self._write_response(Result.OKEY, json.dumps(self._observer.games()))

    COMMAND_MAP = {
        Action.LOGIN: _on_login,
        Action.LOGOUT: _on_logout,
        Action.MAP: _on_get_map,
        Action.MOVE: _on_move,
        Action.TURN: _on_turn,
        Action.OBSERVER: _on_observer,
    }


loop = asyncio.get_event_loop()
# Each client connection will create a new protocol instance.
coro = loop.create_server(GameServerProtocol, SERVER_ADDR, SERVER_PORT)
server = loop.run_until_complete(coro)

# Serve requests until Ctrl+C is pressed.
log(log.INFO, "Serving on {}".format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    log(log.WARNING, "Server stopped by keyboard interrupt...")

# Close the server.
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
