""" Server definitions.
"""
from os import getenv
from enum import IntEnum

SERVER_PORT = getenv('WG_FORGE_SERVER_PORT', 2000)
SERVER_ADDR = getenv('WG_FORGE_SERVER_ADDR', '0.0.0.0')


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
