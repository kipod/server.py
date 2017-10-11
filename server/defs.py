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
