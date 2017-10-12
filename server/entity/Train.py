""" Train entity
"""
import uuid

class Train(object):
    """ train
        has:
         uniqe id -> tid
         position
    """
    def __init__(self, tid=None):
        self.tid = tid if tid else str(uuid.uuid4())
