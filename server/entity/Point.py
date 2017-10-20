"""
Graph vertex - Point entity
"""

class Point(object):
    """
    Point entity
    defined by:
    unique id (idx) - index of point,
    post_id (may be empty) - index of post; defined if with the point associated the post,
    """
    def __init__(self, idx, post_id=None):
        self.idx = idx
        if not post_id is None:
            self.post_id = post_id
