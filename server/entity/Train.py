""" Train entity
"""

class Train(object):
    """ train
        has:
         unique id -> tid
         line_idx - index of line where placed the train
         position - position on the line in a current moment
         speed - speed of the train (-1 or +1). Negative - if the train moves back on the line
    """
    def __init__(self, tid=None, line_idx=None, pos=None, speed=0):
        self.tid = tid if tid else 0
        self.line_idx = line_idx
        self.position = pos
        self.speed = speed
