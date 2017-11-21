""" server definitions
"""
from os import getenv
from enum import IntEnum

SERVER_PORT = getenv('WG_FORGE_SERVER_PORT', 2000)
SERVER_ADDR = getenv('WG_FORGE_SERVER_ADDR', '0.0.0.0')


class Action(IntEnum):
    """ client commands
    """
    LOGIN = 1
    LOGOUT = 2
    MOVE = 3
    TURN = 5
    MAP = 10


class Result(IntEnum):
    """ server response code
    """
    OKEY = 0
    BAD_COMMAND = 1
    RESOURCE_NOT_FOUND = 2
    PATH_NOT_FOUND = 3
    ACCESS_DENIED = 5
