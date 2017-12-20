""" Game server.
"""
import json
from socketserver import ThreadingTCPServer, BaseRequestHandler

from invoke import task

import errors
from defs import SERVER_ADDR, SERVER_PORT, RECEIVE_CHUNK_SIZE, Action, Result
from entity.game import Game
from entity.observer import Observer
from entity.player import Player
from logger import log


def login_required(func):
    def wrapped(self, *args, **kwargs):
        if self.game is None or self.player is None:
            raise errors.AccessDenied("Login required")
        else:
            return func(self, *args, **kwargs)
    return wrapped


class GameServerRequestHandler(BaseRequestHandler):
    def __init__(self, *args, **kwargs):
        self.action = None
        self.message_len = None
        self.message = None
        self.data = None
        self.player = None
        self.game = None
        self.replay = None
        self.observer = None
        self.closed = None
        super(GameServerRequestHandler, self).__init__(*args, **kwargs)

    def setup(self):
        log(log.INFO, "New connection from {}".format(self.client_address))
        self.closed = False

    def handle(self):
        while not self.closed:
            data = self.request.recv(RECEIVE_CHUNK_SIZE)
            if data:
                self.data_received(data)
            else:
                self.closed = True

    def finish(self):
        log(log.WARNING, "Connection from {0} lost".format(self.client_address))
        if self.player is not None:
            self.player.in_game = False
        if self.game is not None:
            if not any([p.in_game for p in self.game.players.values()]):
                self.game.stop()

    def data_received(self, data):
        if self.data:
            data = self.data + data
            self.data = None
        if self.process_data(data):
            log(log.INFO, 'Player: {}, action: {!r}, message:\n{}'.format(
                self.player.idx if self.player is not None else self.client_address,
                Action(self.action), self.message))
            try:
                data = json.loads(self.message)
                if not isinstance(data, dict):
                    raise errors.BadCommand("The command payload is not a dictionary")
                if self.observer:
                    self.write_response(*self.observer.action(self.action, data))
                else:
                    if self.action not in self.COMMAND_MAP:
                        raise errors.BadCommand("No such command")
                    method = self.COMMAND_MAP[self.action]
                    method(self, data)
                    if self.replay and self.action in (Action.MOVE, Action.LOGIN, Action.UPGRADE, ):
                        self.replay.add_action(self.action, self.message)

            # Handle errors:
            except (json.decoder.JSONDecodeError, errors.BadCommand) as err:
                self.error_response(Result.BAD_COMMAND, err)
            except errors.AccessDenied as err:
                self.error_response(Result.ACCESS_DENIED, err)
            except errors.NotReady as err:
                self.error_response(Result.NOT_READY, err)
            except errors.Timeout as err:
                self.error_response(Result.TIMEOUT, err)
            except errors.ResourceNotFound as err:
                self.error_response(Result.RESOURCE_NOT_FOUND, err)
            except Exception:
                log(log.EXCEPTION, "Got unhandled exception on client command execution")
                self.error_response(Result.INTERNAL_SERVER_ERROR)
            finally:
                self.action = None

    def process_data(self, data):
        """ Parses input command.
        returns: True if command parsing completed
        """
        # Read action [4 bytes]:
        if not self.action:
            if len(data) < 4:
                self.data = data
                return False
            self.action = Action(int.from_bytes(data[0:4], byteorder='little'))
            self.message_len = 0
            data = data[4:]
            if self.action in (Action.LOGOUT, Action.OBSERVER):  # Commands without data.
                self.data = b''
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

    def write_response(self, result, message=None):
        resp_message = '' if message is None else message
        log(log.DEBUG, 'Player: {}, result: {!r}, message:\n{}'.format(
            self.player.idx if self.player is not None else self.client_address,
            result, resp_message))
        self.request.sendall(result.to_bytes(4, byteorder='little'))
        self.request.sendall(len(resp_message).to_bytes(4, byteorder='little'))
        self.request.sendall(resp_message.encode('utf-8'))

    def error_response(self, result, error=None):
        if error is not None:
            error_msg = str(error)
            response_msg = json.dumps({'error': error_msg})
            log(log.ERROR, error_msg)
        else:
            response_msg = ''
        self.write_response(result, response_msg)

    @staticmethod
    def check_keys(data: dict, keys, agg_func=all):
        if not agg_func([k in data for k in keys]):
            raise errors.BadCommand(
                "The command payload does not contain all needed keys, following keys are expected: {}".format(keys))
        else:
            return True

    def on_login(self, data: dict):
        self.check_keys(data, ['name'])
        game_name = 'Game of {}'.format(data['name'])
        num_players = 1
        if 'game' in data and self.check_keys(data, ['num_players']):
            game_name = data['game']
            num_players = data['num_players']

        game = Game.create(game_name, num_players)
        if game.num_players != num_players:
            raise errors.BadCommand(
                "Incorrect players number requested, game: {}, game players number: {}, "
                "requested players number: {}".format(game_name, game.num_players, num_players)
            )

        security_key = data.get('security_key', None)
        player = Player.create(data['name'], security_key)
        if player.security_key != security_key:
            raise errors.AccessDenied("Security key mismatch")

        game.add_player(player)
        self.game = game
        self.player = player
        self.replay = game.replay

        log(log.INFO, "Login player: {}".format(player))
        message = self.player.to_json_str()
        self.write_response(Result.OKEY, message)

    @login_required
    def on_logout(self, _):
        log(log.INFO, "Logout player: {}".format(self.player.name))
        self.player.in_game = False
        if not any([p.in_game for p in self.game.players.values()]):
            self.game.stop()
        self.closed = True
        self.write_response(Result.OKEY)

    @login_required
    def on_get_map(self, data: dict):
        self.check_keys(data, ['layer'])
        message = self.game.get_map_layer(self.player, data['layer'])
        self.write_response(Result.OKEY, message)

    @login_required
    def on_move(self, data: dict):
        self.check_keys(data, ['train_idx', 'speed', 'line_idx'])
        self.game.move_train(self.player, data['train_idx'], data['speed'], data['line_idx'])
        self.write_response(Result.OKEY)

    @login_required
    def on_turn(self, _):
        self.game.turn(self.player)
        self.write_response(Result.OKEY)

    @login_required
    def on_upgrade(self, data: dict):
        self.check_keys(data, ['train', 'post'], agg_func=any)
        self.game.make_upgrade(
            self.player, post_ids=data.get('post', []), train_ids=data.get('train', [])
        )
        self.write_response(Result.OKEY)

    def on_observer(self, _):
        if self.game or self.observer:
            raise errors.BadCommand("Impossible connect as observer")
        else:
            self.observer = Observer()
            self.write_response(Result.OKEY, json.dumps(self.observer.games()))

    COMMAND_MAP = {
        Action.LOGIN: on_login,
        Action.LOGOUT: on_logout,
        Action.MAP: on_get_map,
        Action.MOVE: on_move,
        Action.UPGRADE: on_upgrade,
        Action.TURN: on_turn,
        Action.OBSERVER: on_observer,
    }


@task
def run_server(_, address=SERVER_ADDR, port=SERVER_PORT):
    """ Launches 'WG Forge' TCP server.
    """
    server = ThreadingTCPServer((address, port), GameServerRequestHandler)
    log(log.INFO, "Serving on {}".format(server.socket.getsockname()))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log(log.WARNING, "Server stopped by keyboard interrupt...")
    finally:
        try:
            Game.stop_all_games()
        finally:
            server.shutdown()
            server.server_close()
