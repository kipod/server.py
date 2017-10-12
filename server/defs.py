""" server definitions
"""
from enum import IntEnum
SERVER_PORT = 2000


class Action(IntEnum):
    """ client commands
    """
    LOGIN = 1
    LOGOUT = 2
    RUN = 3
    STOP = 4
    NEXT = 5
    MAP = 10


class Result(IntEnum):
    """ server response code
    """
    OKEY = 0
    BAD_COMMAND = 1
    RESOURCE_NOT_FOUND = 2
    PATH_NOT_FOUND = 3
    ACCESS_DENIED = 5
