from attrdict import AttrDict

TICK_TIME = 10
MAP_NAME = 'map02'
DEFAULT_TRAINS_COUNT = 2
HIJACKERS_ASSAULT_PROBABILITY = 0
HIJACKERS_POWER_RANGE = (1, 3)
PARASITES_ASSAULT_PROBABILITY = 0
PARASITES_POWER_RANGE = (1, 3)

TOWN_LEVELS = AttrDict({
    1: {
        'population_capacity': 10,
        'product_capacity': 200,
        'armor_capacity': 100,
        'next_level_price': 100,
    },
    2: {
        'population_capacity': 20,
        'product_capacity': 400,
        'armor_capacity': 200,
        'next_level_price': 200,
    },
    3: {
        'population_capacity': 40,
        'product_capacity': 800,
        'armor_capacity': 400,
        'next_level_price': None,
    },
})

TRAIN_LEVELS = AttrDict({
    1: {
        'goods_capacity': 40,
        # 'fuel_capacity': 400,
        # 'fuel_consumption': 1,
        'next_level_price': 40,
    },
    2: {
        'goods_capacity': 80,
        # 'fuel_capacity': 800,
        # 'fuel_consumption': 1,
        'next_level_price': 80,
    },
    3: {
        'goods_capacity': 160,
        # 'fuel_capacity': 1600,
        # 'fuel_consumption': 1,
        'next_level_price': None,
    },
})
