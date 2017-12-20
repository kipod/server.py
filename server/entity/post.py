from enum import IntEnum

from game_config import CONFIG


class PostType(IntEnum):
    """ Types of a Post.
    TOWN - population lives here, eats 'product', uses 'armor' for defense and evolution.
    MARKET - provides players's trains with 'product' resource.
    STORAGE - provides players's trains with 'armor' resource.
    """
    TOWN = 1
    MARKET = 2
    STORAGE = 3


class Post(object):
    """ Post object represents dynamic object on the map.
    Describes additional parameters of the Point. Post can belong to only one Point.

    Initialization:
        idx: unique index of the Post
        name: unique name of the Post
        post_type: type of the Post (PostType)
        population: population in the Town (only for TOWN)
        armor: defend points (for TOWN and STORAGE)
        product: production points (for TOWN and MARKET)
        replenishment: replenishment of the resource per game tick (for MARKET and STORAGE)
        level: current level of the Town (only for TOWN)
        player_id: unique index of the Player which is owner of the Town (only for TOWN)
        point_id: unique index of the Point where the Post is placed

    Has attributes:
        idx: unique index of the Post
        name: unique name of the Post
        type: type of the Post (PostType)
        point_id: unique index of the Point where the Post is placed
        event: all events happened with the Post
        level: current level of the Town (only for TOWN)
        population: population in the Town (only for TOWN)
        product: production points (for TOWN and MARKET)
        armor: defend points (for TOWN and STORAGE)
        player_id: unique index of the Player which is owner of the Town (only for TOWN)
        population_capacity: max limit of population (only for TOWN)
        product_capacity: max limit of product (for TOWN and MARKET)
        armor_capacity: max limit of armor (for TOWN and STORAGE)
        next_level_price: armor amount which player have to pay to get next level (only for TOWN)
        replenishment: replenishment of the resource per game tick (for MARKET and STORAGE)
    """
    def __init__(self, idx, name, post_type, population=0, armor=0, product=0,
                 replenishment=1, level=1, player_id=None, point_id=None):
        self.idx = idx
        self.name = name
        self.type = PostType(post_type)
        self.point_id = point_id
        self.event = []

        if self.type == PostType.TOWN:
            self.level = level
            self.population = population
            self.product = product
            self.armor = armor
            self.player_id = player_id
            # Additional attributes from game_config:
            for key, value in CONFIG.TOWN_LEVELS[self.level].items():
                setattr(self, key, value)

        if self.type == PostType.MARKET:
            self.product_capacity = product
            self.product = product
            self.replenishment = replenishment

        if self.type == PostType.STORAGE:
            self.armor_capacity = armor
            self.armor = armor
            self.replenishment = replenishment

    def set_level(self, next_lvl):
        self.level = next_lvl
        for key, value in CONFIG.TOWN_LEVELS[self.level].items():
            setattr(self, key, value)

    def __repr__(self):
        return "<Post(idx={}, name='{}', type={!r}, point_id={})>".format(
            self.idx, self.name, self.type, self.point_id
        )
