"""
Game server
"""
import asyncio
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
        self._game = Game()
        self._game.add_player(self._player)

    def connection_made(self, transport):
        self.peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(self.peername))
        self.transport = transport


    def connection_lost(self, exc):
        print('Connection from {} \n\tReson: {}'.format(self.peername, exc))

    def data_received(self, data):
        if self.data:
            data = self.data + data
            self.data = b""
        if self._process_data(data):
            method = self.COMMAND_MAP[self._action]
            if method:
                method(self, self.message)
            self._action = None

    def _process_data(self, data):
        """
        parsing input command
        returns True if command parsing complited
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

    def _on_login(self, name):
        self._player = Player(name)
        self._write_respose(Result.OKEY)

    def _on_logout(self, _):
        self._write_respose(Result.OKEY)
        print('Close the client socket')
        self.transport.close()

    def _on_get_map(self, layer):
        if int(layer) == 0: #terrain = static objects
            message = self._game.map.to_json_str()
            self._write_respose(Result.OKEY, message)
        elif int(layer) == 1: #dynamic objects
            message = ''
            self._write_respose(Result.OKEY, message)
        else:
            self._write_respose(Result.RESOURCE_NOT_FOUND)

    COMMAND_MAP = {
        Action.LOGIN : _on_login,
        Action.LOGOUT : _on_logout,
        Action.MAP : _on_get_map
    }


loop = asyncio.get_event_loop()
# Each client connection will create a new protocol instance
coro = loop.create_server(GameServerProtocol, '0.0.0.0', SERVER_PORT)
server = loop.run_until_complete(coro)

# Serve requests until Ctrl+C is pressed
print('Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()