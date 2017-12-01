""" DB map generator.
"""
from invoke import task

from db.models import MapBase, Map, Line, Point, Post
from db.session import MapSession
from entity.post import PostType


class DbMap(object):
    """ Contains helpers for map generation.
    """
    def __init__(self):
        self.reset_db()
        self.session = MapSession()
        self.current_map_id = None

    def reset_db(self):
        """ Re-applies DB schema.
        """
        MapBase.metadata.drop_all()
        MapBase.metadata.create_all()

    def add_map(self, size_x, size_y, name=''):
        """ Creates new Map in DB.
        """
        new_map = Map(name=name, size_x=size_x, size_y=size_y)
        self.session.add(new_map)
        self.session.commit()  # Commit to get map's id.
        self.current_map_id = new_map.id
        return self.current_map_id

    def add_line(self, length, p0, p1, map_id=None):
        """ Creates new Line in DB.
        """
        _map_id = self.current_map_id if map_id is None else map_id
        new_line = Line(len=length, p0=p0, p1=p1, map_id=_map_id)
        self.session.add(new_line)
        self.session.commit()  # Commit to get line's id.
        return new_line.id

    def add_point(self, map_id=None, x=0, y=0):
        """ Creates new Point in DB.
        """
        _map_id = self.current_map_id if map_id is None else map_id
        new_point = Point(map_id=_map_id, x=x, y=y)
        self.session.add(new_point)
        self.session.commit()  # Commit to get point's id.
        return new_point.id

    def add_post(self, point_id, name, type_p, population=0, armor=0, product=0, replenishment=1, map_id=None):
        """ Creates new Post in DB.
        """
        _map_id = self.current_map_id if map_id is None else map_id
        new_post = Post(name=name, type=type_p, population=population, armor=armor, product=product,
                        replenishment=replenishment, map_id=_map_id, point_id=point_id)
        self.session.add(new_post)
        self.session.commit()  # Commit to get post's id.
        return new_post.id

    def close(self):
        """ Closes and commits session.
        """
        self.session.commit()
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()


def generate_map01(db):
    """ Generates 'map01'. See 'map01.png'.
    """
    # Map:
    db.add_map(name='map01', size_x=330, size_y=248)

    # Points:
    p1 = db.add_point(x=75, y=16)
    p2 = db.add_point(x=250, y=16)
    p3 = db.add_point(x=312, y=120)
    p4 = db.add_point(x=250, y=220)
    p5 = db.add_point(x=100, y=220)
    p6 = db.add_point(x=10, y=120)
    p7 = db.add_point(x=134, y=70)
    p8 = db.add_point(x=200, y=70)
    p9 = db.add_point(x=235, y=120)
    p10 = db.add_point(x=198, y=160)
    p11 = db.add_point(x=134, y=160)
    p12 = db.add_point(x=85, y=120)

    # Posts:
    db.add_post(p1, 'town-one', PostType.TOWN, population=10)
    db.add_post(p7, 'market-one', PostType.MARKET, product=20, replenishment=1)

    # Lines:
    db.add_line(10, p1, p7)  # 1: 1-7
    db.add_line(10, p8, p2)  # 2: 8-2
    db.add_line(10, p9, p3)  # 3: 9-3
    db.add_line(10, p10, p4)  # 4: 10-4
    db.add_line(10, p11, p5)  # 5: 11-5
    db.add_line(10, p12, p6)  # 6: 12-6
    db.add_line(10, p7, p8)  # 7: 7-8
    db.add_line(10, p8, p9)  # 8: 8-9
    db.add_line(10, p9, p10)  # 9: 9-10
    db.add_line(10, p10, p11)  # 10: 10-11
    db.add_line(10, p11, p12)  # 11: 11-12
    db.add_line(10, p12, p7)  # 12: 12-7


def generate_map02(db):
    """ Generates 'map02'. See 'map02.png'.
    """
    # Map:
    db.add_map(name='map02', size_x=330, size_y=248)

    # Points:
    p1 = db.add_point(x=75, y=16)
    p2 = db.add_point(x=250, y=16)
    p3 = db.add_point(x=312, y=120)
    p4 = db.add_point(x=250, y=220)
    p5 = db.add_point(x=100, y=220)
    p6 = db.add_point(x=10, y=120)
    p7 = db.add_point(x=134, y=70)
    p8 = db.add_point(x=200, y=70)
    p9 = db.add_point(x=235, y=120)
    p10 = db.add_point(x=198, y=160)
    p11 = db.add_point(x=134, y=160)
    p12 = db.add_point(x=85, y=120)

    # Posts:
    db.add_post(p1, 'town-one', PostType.TOWN, population=3, product=35)
    db.add_post(p4, 'market-big', PostType.MARKET, product=36, replenishment=2)
    db.add_post(p5, 'market-medium', PostType.MARKET, product=28, replenishment=1)
    db.add_post(p7, 'market-small', PostType.MARKET, product=5, replenishment=1)

    # Lines:
    db.add_line(1, p1, p7)  # 1: 1-7
    db.add_line(1, p8, p2)  # 2: 8-2
    db.add_line(1, p9, p3)  # 3: 9-3
    db.add_line(1, p10, p4)  # 4: 10-4
    db.add_line(1, p11, p5)  # 5: 11-5
    db.add_line(2, p12, p6)  # 6: 12-6
    db.add_line(1, p7, p8)  # 7: 7-8
    db.add_line(2, p8, p9)  # 8: 8-9
    db.add_line(2, p9, p10)  # 9: 9-10
    db.add_line(1, p10, p11)  # 10: 10-11
    db.add_line(3, p11, p12)  # 11: 11-12
    db.add_line(1, p12, p7)  # 12: 12-7
    db.add_line(2, p1, p2)  # 13: 1-2
    db.add_line(2, p2, p3)  # 14: 2-3
    db.add_line(1, p3, p4)  # 15: 3-4
    db.add_line(3, p4, p5)  # 16: 4-5
    db.add_line(1, p5, p6)  # 17: 5-6
    db.add_line(3, p6, p1)  # 18: 6-1


MAP_GENERATORS = {
    'map01': generate_map01,
    'map02': generate_map02,
}


@task
def generate_map(ctx, map_name=None):
    with DbMap() as db:
        maps_to_generate = MAP_GENERATORS.keys() if map_name is None else [map_name, ]
        for curr_map in maps_to_generate:
            map_generator = MAP_GENERATORS[curr_map]
            map_generator(db)
            print("Map '{}' has been generated.".format(curr_map))
