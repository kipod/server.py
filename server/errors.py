""" Server errors.
"""


class WgForgeServerError(Exception):
    """ Base server exception.
    """
    pass


class BadCommand(WgForgeServerError):
    pass


class NotReady(WgForgeServerError):
    pass


class Timeout(WgForgeServerError):
    pass


class AccessDenied(WgForgeServerError):
    """ Access to requested resource denied.
    """
    pass


class ResourceNotFound(WgForgeServerError):
    pass
