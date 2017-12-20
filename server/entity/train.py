""" Train entity
"""
from game_config import CONFIG


class Train(object):
    """ Train object represents train in the game which is able to transport some goods.

    Initialization:
        idx: unique index of the Train
        line_idx: unique index of line where the Train is placed
        position: position on the line at the current moment
        speed: speed of the Train (-1 or +1), negative - if the train is moving back on the line
        player_id: unique index of the Player which is owner of the Train
        level: current level of the Train
        goods: quantity of some goods in the train at the current moment
        post_type: PostType where first goods have been loaded into the train

    Has attributes:
        idx: unique index of the Train
        line_idx: unique index of line where the Train is placed
        position: position on the line at the current moment
        speed: speed of the Train (-1 or +1), negative - if the train is moving back on the line
        player_id: unique index of the Player which is owner of the Train
        level: current level of the Train
        goods_capacity: maximum quantity of goods that the train can transport
        fuel: fuel amount in the train's tank at the current moment
        fuel_capacity: fuel tank size
        fuel_consumption: quantity of fuel that the train consumes per one unit of distance
        next_level_price: armor amount which player have to pay to get next level
        goods: quantity of some goods in the train at the current moment
        post_type: PostType where first goods have been loaded into the train
        event: all events happened with the Train
        cooldown: the Train is blocked for this quantity of game ticks
    """
    def __init__(self, idx, line_idx=None, position=None, speed=0, player_id=None, level=1, goods=0, post_type=None):
        self.idx = idx
        self.line_idx = line_idx
        self.position = position
        self.speed = speed
        self.player_id = player_id
        self.level = level
        # Additional attributes from game_config:
        for key, value in CONFIG.TRAIN_LEVELS[self.level].items():
            setattr(self, key, value)
        # self.fuel = self.fuel_capacity if hasattr(self, 'fuel_capacity') else 0
        self.goods = goods
        self.post_type = post_type
        self.event = []
        self.cooldown = 0

    def set_level(self, next_lvl):
        self.level = next_lvl
        for key, value in CONFIG.TRAIN_LEVELS[self.level].items():
            setattr(self, key, value)

    def __repr__(self):
        return (
            "<Train(idx={}, line_idx={}, position={}, speed={}, player_id={}, "
            "level={}, goods={}, post_type={}, cooldown={})>".format(
                self.idx, self.line_idx, self.position, self.speed, self.player_id,
                self.level, self.goods, self.post_type, self.cooldown
            )
        )
