"""
Post - dynamic object on the map.
Describes additional parameters of the Point.
Post can belong to only one Point.
"""
from enum import IntEnum

class Type(IntEnum):
    """ types of a post """
    TOWN = 1
    MARKET = 2


class Post(object):
    """
    Post object
    * name - name of this post
    * type - post type (Post.Type)
    * population - population in the town (only for TOWN)
    * armor - defend points (only for TOWN)
    * product - production points (for TOWN and SHOP)
    """
    def __init__(self, idx, name, post_type, population, armor, product, player=None, replenishment = 1):
        self.idx = idx
        self.name = name
        self.type = Type(post_type)
        if self.type == Type.TOWN:
            self.population = population
            self.armor = armor
        self.product = product
        if self.type == Type.MARKET:
            self.product_capacity = product
            self.replenishment = replenishment
        if player is not None:
            self.player = player
