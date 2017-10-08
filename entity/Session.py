"""
entity network session
"""
import uuid

class Session(object):
    """ Network session
    """
    def __init__(self, player, sid=None):
        self.player = player
        self.sid = sid if sid else str(uuid.uuid4())
