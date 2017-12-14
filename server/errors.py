""" Server errors.
"""


class WgForgeServerError(Exception):
    """ Base server exception.
    """
    pass


class BadCommand(WgForgeServerError):
    pass


class IllegalCommand(WgForgeServerError):
    pass


class GameNotReady(WgForgeServerError):
    pass


class GameTimeout(WgForgeServerError):
    pass


class GameAccessDenied(WgForgeServerError):
    """ Access to requested resource denied.
    """
    pass
