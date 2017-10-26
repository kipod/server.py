"""
Game server
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import asyncio
import json
from log import LOG
from defs import SERVER_PORT, Action, Result
from entity.Player import Player
from entity.Game import Game

class GameServerProtocol(asyncio.Protocol):
    def __init__(self):
        asyncio.Protocol.__init__(self)
        self._action = None
        self.message_len = None
        self.message = None
        self.data = None
        self._player = None
        self._game = None

    def connection_made(self, transport):
        self.peername = transport.get_extra_info('peername')
        LOG(LOG.INFO, 'Connection from %s', self.peername)
        self.transport = transport


    def connection_lost(self, exc):
        LOG(LOG.WARNING, 'Connection from %s lost. Reason:%s', self.peername, exc)

    def data_received(self, data):
        if self.data:
            data = self.data + data
            self.data = b""
        if self._process_data(data):
            LOG(LOG.INFO, str(Action(self._action)))
            method = self.COMMAND_MAP[self._action]
            if method:
                method(self, self.message)
            self._action = None

    def _process_data(self, data):
        """
        parsing input command
        returns True if command parsing completed
        """
        # read action [4 bytes]
        if not self._action:
            if len(data) < 4:
                self.data = data
                return False
            self._action = Action(int.from_bytes(data[0:4], byteorder = 'little'))
            self.message_len = 0
            data = data[4:]
            if self._action in (Action.LOGOUT, ): # commands without data
                self.data = data
                return True
        # read size of message
        if not self.message_len:
            if len(data) < 4:
                self.data = data
                return False
            self.message_len = int.from_bytes(data[0:4], byteorder = 'little')
            data = data[4:]
        # read message
        if len(data) < self.message_len:
            self.data = data
            return False
        self.message = data[0:self.message_len].decode('utf-8')
        self.data = data[self.message_len:]
        return True

    def _write_respose(self, result, message=None):
        self.transport.write(result.to_bytes(4, byteorder='little'))
        if message:
            self.transport.write(len(message).to_bytes(4, byteorder='little'))
            self.transport.write(message.encode('utf-8'))

    def _on_login(self, json_string_data):
        data = json.loads(json_string_data)
        if 'name' in data:
            self._game = Game.create('Game of {}'.format(data['name']))
            self._player = Player(data['name'])
            self._game.add_player(self._player)
            LOG(LOG.INFO, "Login player: %s", data['name'])
            message = self._player.to_json_str()
            self._write_respose(Result.OKEY, message)
        else:
            self._write_respose(Result.BAD_COMMAND)

    def _on_logout(self, _):
        self._write_respose(Result.OKEY)
        LOG(LOG.INFO, 'Logout. Player:%s', self._player.name)
        self.transport.close()
        self._game.stop()
        del self._game
        self._game = None

    def _on_get_map(self, json_string_data):
        data = json.loads(json_string_data)
        if 'layer' in data.keys():
            layer = data['layer']
            LOG(LOG.INFO, "Load map layer=%d", layer)
            message = self._game.map.layer_to_json_str(layer)
            self._write_respose(Result.OKEY, message)
        else:
            self._write_respose(Result.BAD_COMMAND)

    def _on_move(self, json_string_data):
        data = json.loads(json_string_data)
        res = self._game.move_train(data['train_idx'],
                                    data['speed'],
                                    data['line_idx'])
        self._write_respose(res)

    def _on_turn(self, _):
        self._game.turn()
        self._write_respose(Result.OKEY)

    COMMAND_MAP = {
        Action.LOGIN : _on_login,
        Action.LOGOUT : _on_logout,
        Action.MAP : _on_get_map,
        Action.MOVE : _on_move,
        Action.TURN : _on_turn
    }


loop = asyncio.get_event_loop()
# Each client connection will create a new protocol instance
coro = loop.create_server(GameServerProtocol, '0.0.0.0', SERVER_PORT)
SERVER = loop.run_until_complete(coro)

# Serve requests until Ctrl+C is pressed
LOG(LOG.INFO, 'Serving on %s', SERVER.sockets[0].getsockname())
try:
    loop.run_forever()
except KeyboardInterrupt:
    LOG(LOG.WARNING, 'Server stopped by keyboard interrupt...')

# Close the server
SERVER.close()
loop.run_until_complete(SERVER.wait_closed())
loop.close()
