""" Server definitions.
"""
from enum import IntEnum
from os import getenv, path

SERVER_PORT = int(getenv('WG_FORGE_SERVER_PORT', 2000))
SERVER_ADDR = getenv('WG_FORGE_SERVER_ADDR', '0.0.0.0')
MAP_DB_URI = getenv('MAP_DB_URI', 'sqlite:///' + path.join(path.dirname(path.realpath(__file__)), 'db/map.db'))
REPLAY_DB_URI = getenv('MAP_DB_URI', 'sqlite:///' + path.join(path.dirname(path.realpath(__file__)), 'db/replay.db'))
DB_URI = {
    'map': MAP_DB_URI,
    'replay': REPLAY_DB_URI,
}
RECEIVE_CHUNK_SIZE = 1024


class Action(IntEnum):
    """ Client commands.
    """
    LOGIN = 1
    LOGOUT = 2
    MOVE = 3
    UPGRADE = 4
    TURN = 5
    MAP = 10
    OBSERVER = 100
    GAME = 101

    # This actions are not available for client:
    EVENT = 102


class Result(IntEnum):
    """ Server response codes.
    """
    OKEY = 0
    BAD_COMMAND = 1
    RESOURCE_NOT_FOUND = 2
    ACCESS_DENIED = 5
    NOT_READY = 21
    TIMEOUT = 258
    INTERNAL_SERVER_ERROR = 500
