""" Post - dynamic object on the map.
Describes additional parameters of the Point.
Post can belong to only one Point.
"""
from enum import IntEnum


class PostType(IntEnum):
    """ Types of a post.
    """
    TOWN = 1
    MARKET = 2


class Post(object):
    """ Post object
    * name - name of this post
    * type - post type (PostType)
    * population - population in the town (only for TOWN)
    * armor - defend points (only for TOWN)
    * product - production points (for TOWN and SHOP)
    """
    def __init__(self, idx, name, post_type, population, armor, product, replenishment=1):
        self.idx = idx
        self.name = name
        self.type = PostType(post_type)
        if self.type == PostType.TOWN:
            self.population = population
            self.armor = armor
        self.product = product
        if self.type == PostType.MARKET:
            self.product_capacity = product
            self.replenishment = replenishment
