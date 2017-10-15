"""
Graph vertex - Point entity
"""

class Point(object):
    """
    Point entity
    defined by:
    unique id (idx),
    name (may be empty),
    post type ( number, TBD ),
    population (for the Town type),
    armor (for the Town type),
    product (for the Shop type)
    """
    def __init__(self, idx, name='', post_type=None,
                 population=None, armor=None, product=None):
        self.idx = idx
        if name:
            self.name = name
            self.post_type = post_type
            self.population = population
            self.armor = armor
            self.product = product
