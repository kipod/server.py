""" Train entity.
"""


class Train(object):
    """ train
        has:
         unique id -> tid
         line_idx - index of line where placed the train
         position - position on the line in a current moment
         speed - speed of the train (-1 or +1). Negative - if the train moves back on the line
         capacity - maximum product that train can transport
         product - quantity of product transports by train
    """
    def __init__(self, idx=None, line_idx=None, pos=None, speed=0, player=None):
        self.idx = idx if idx else 0
        self.line_idx = line_idx
        self.position = pos
        self.speed = speed
        self.player_id = None
        if player is not None:
            self.player_id = player.idx
        self.capacity = 200
        self.product = 0
