""" Server definitions.
"""
from enum import IntEnum
from os import getenv, path

SERVER_PORT = getenv('WG_FORGE_SERVER_PORT', 2000)
SERVER_ADDR = getenv('WG_FORGE_SERVER_ADDR', '0.0.0.0')
MAP_DB_URI = getenv('MAP_DB_URI', 'sqlite:///' + path.join(path.dirname(path.realpath(__file__)), 'db/map.db'))
REPLAY_DB_URI = getenv('MAP_DB_URI', 'sqlite:///' + path.join(path.dirname(path.realpath(__file__)), 'db/replay.db'))


class Action(IntEnum):
    """ Client commands.
    """
    LOGIN = 1
    LOGOUT = 2
    MOVE = 3
    TURN = 5
    MAP = 10
    OBSERVER = 100
    GAME = 101


class Result(IntEnum):
    """ Server response codes.
    """
    OKEY = 0
    BAD_COMMAND = 1
    RESOURCE_NOT_FOUND = 2
    PATH_NOT_FOUND = 3
    ACCESS_DENIED = 5


# Server errors:


class WgForgeServerError(Exception):
    pass


class BadCommandError(WgForgeServerError):
    pass
