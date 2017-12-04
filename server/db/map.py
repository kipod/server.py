""" DB map generator.
"""
from invoke import task
from invoke.exceptions import Failure as InvFailure

from db.models import MapBase, Map, Line, Point, Post
from db.session import MapSession
from entity.post import PostType


class DbMap(object):
    """ Contains helpers for map generation.
    """
    def __init__(self):
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
    db.add_post(p1, 'town-one', PostType.TOWN, population=5, product=35)
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


def generate_map03(db):
    """ Generates 'map03'. See 'map03.png'.
    """
    # Map:
    db.add_map(name='map03', size_x=200, size_y=200)

    # Points:
    p1  = db.add_point(x=10,  y=10)
    p2  = db.add_point(x=30,  y=10)
    p3  = db.add_point(x=50,  y=10)
    p4  = db.add_point(x=70,  y=10)
    p5  = db.add_point(x=90,  y=10)
    p6  = db.add_point(x=110, y=10)
    p7  = db.add_point(x=130, y=10)
    p8  = db.add_point(x=150, y=10)
    p9  = db.add_point(x=170, y=10)
    p10 = db.add_point(x=190, y=10)

    p11 = db.add_point(x=10,  y=30)
    p12 = db.add_point(x=30,  y=30)
    p13 = db.add_point(x=50,  y=30)
    p14 = db.add_point(x=70,  y=30)
    p15 = db.add_point(x=90,  y=30)
    p16 = db.add_point(x=110, y=30)
    p17 = db.add_point(x=130, y=30)
    p18 = db.add_point(x=150, y=30)
    p19 = db.add_point(x=170, y=30)
    p20 = db.add_point(x=190, y=30)

    p21 = db.add_point(x=10,  y=50)
    p22 = db.add_point(x=30,  y=50)
    p23 = db.add_point(x=50,  y=50)
    p24 = db.add_point(x=70,  y=50)
    p25 = db.add_point(x=90,  y=50)
    p26 = db.add_point(x=110, y=50)
    p27 = db.add_point(x=130, y=50)
    p28 = db.add_point(x=150, y=50)
    p29 = db.add_point(x=170, y=50)
    p30 = db.add_point(x=190, y=50)

    p31 = db.add_point(x=10,  y=70)
    p32 = db.add_point(x=30,  y=70)
    p33 = db.add_point(x=50,  y=70)
    p34 = db.add_point(x=70,  y=70)
    p35 = db.add_point(x=90,  y=70)
    p36 = db.add_point(x=110, y=70)
    p37 = db.add_point(x=130, y=70)
    p38 = db.add_point(x=150, y=70)
    p39 = db.add_point(x=170, y=70)
    p40 = db.add_point(x=190, y=70)

    p41 = db.add_point(x=10,  y=90)
    p42 = db.add_point(x=30,  y=90)
    p43 = db.add_point(x=50,  y=90)
    p44 = db.add_point(x=70,  y=90)
    p45 = db.add_point(x=90,  y=90)
    p46 = db.add_point(x=110, y=90)
    p47 = db.add_point(x=130, y=90)
    p48 = db.add_point(x=150, y=90)
    p49 = db.add_point(x=170, y=90)
    p50 = db.add_point(x=190, y=90)

    p41 = db.add_point(x=10,  y=110)
    p42 = db.add_point(x=30,  y=110)
    p43 = db.add_point(x=50,  y=110)
    p44 = db.add_point(x=70,  y=110)
    p45 = db.add_point(x=90,  y=110)
    p46 = db.add_point(x=110, y=110)
    p47 = db.add_point(x=130, y=110)
    p48 = db.add_point(x=150, y=110)
    p49 = db.add_point(x=170, y=110)
    p50 = db.add_point(x=190, y=110)

    p51 = db.add_point(x=10,  y=130)
    p52 = db.add_point(x=30,  y=130)
    p53 = db.add_point(x=50,  y=130)
    p54 = db.add_point(x=70,  y=130)
    p55 = db.add_point(x=90,  y=130)
    p56 = db.add_point(x=110, y=130)
    p57 = db.add_point(x=130, y=130)
    p58 = db.add_point(x=150, y=130)
    p59 = db.add_point(x=170, y=130)
    p60 = db.add_point(x=190, y=130)

    p61 = db.add_point(x=10,  y=150)
    p62 = db.add_point(x=30,  y=150)
    p63 = db.add_point(x=50,  y=150)
    p64 = db.add_point(x=70,  y=150)
    p65 = db.add_point(x=90,  y=150)
    p66 = db.add_point(x=110, y=150)
    p67 = db.add_point(x=130, y=150)
    p68 = db.add_point(x=150, y=150)
    p69 = db.add_point(x=170, y=150)
    p70 = db.add_point(x=190, y=150)

    p71 = db.add_point(x=10,  y=170)
    p72 = db.add_point(x=30,  y=170)
    p73 = db.add_point(x=50,  y=170)
    p74 = db.add_point(x=70,  y=170)
    p75 = db.add_point(x=90,  y=170)
    p76 = db.add_point(x=110, y=170)
    p77 = db.add_point(x=130, y=170)
    p78 = db.add_point(x=150, y=170)
    p79 = db.add_point(x=170, y=170)
    p80 = db.add_point(x=190, y=170)

    p81 = db.add_point(x=10,  y=190)
    p82 = db.add_point(x=30,  y=190)
    p83 = db.add_point(x=50,  y=190)
    p84 = db.add_point(x=70,  y=190)
    p85 = db.add_point(x=90,  y=190)
    p86 = db.add_point(x=110, y=190)
    p87 = db.add_point(x=130, y=190)
    p88 = db.add_point(x=150, y=190)
    p89 = db.add_point(x=170, y=190)
    p90 = db.add_point(x=190, y=190)


    # Posts:
    db.add_post(p1, 'town-one', PostType.TOWN, population=3, product=350, armor=100)
    db.add_post(p89, 'market-big', PostType.MARKET, product=500, replenishment=10)
    db.add_post(p49, 'market-medium', PostType.MARKET, product=250, replenishment=10)
    db.add_post(p12, 'market-small', PostType.MARKET, product=50, replenishment=5)
    db.add_post(p32, 'storage-small', PostType.STORAGE, armor=20, replenishment=1)
    db.add_post(p56, 'storage-big', PostType.STORAGE, armor=100, replenishment=5)

    # Lines:
    db.add_line(4, p1, p2)
    db.add_line(4, p2, p3)
    db.add_line(4, p3, p4)
    db.add_line(4, p4, p5)
    db.add_line(4, p5, p6)
    db.add_line(4, p6, p7)
    db.add_line(4, p7, p8)
    db.add_line(4, p8, p9)
    db.add_line(4, p9, p10)

    db.add_line(5, p1, p11)
    db.add_line(5, p2, p12)
    db.add_line(5, p3, p13)
    db.add_line(5, p4, p14)
    db.add_line(5, p5, p15)
    db.add_line(5, p6, p16)
    db.add_line(5, p7, p17)
    db.add_line(5, p8, p18)
    db.add_line(5, p9, p19)
    db.add_line(5, p10, p20)


    db.add_line(4, p11, p12)
    db.add_line(4, p12, p13)
    db.add_line(4, p13, p14)
    db.add_line(4, p14, p15)
    db.add_line(4, p15, p16)
    db.add_line(4, p16, p17)
    db.add_line(4, p17, p18)
    db.add_line(4, p18, p19)
    db.add_line(4, p19, p20)

    db.add_line(5, p11, p21)
    db.add_line(5, p12, p22)
    db.add_line(5, p13, p23)
    db.add_line(5, p14, p24)
    db.add_line(5, p15, p25)
    db.add_line(5, p16, p26)
    db.add_line(5, p17, p27)
    db.add_line(5, p18, p28)
    db.add_line(5, p19, p29)
    db.add_line(5, p20, p30)


    db.add_line(4, p21, p22)
    db.add_line(4, p22, p23)
    db.add_line(4, p23, p24)
    db.add_line(4, p24, p25)
    db.add_line(4, p25, p26)
    db.add_line(4, p26, p27)
    db.add_line(4, p27, p28)
    db.add_line(4, p28, p29)
    db.add_line(4, p29, p30)

    db.add_line(5, p21, p31)
    db.add_line(5, p22, p32)
    db.add_line(5, p23, p33)
    db.add_line(5, p24, p34)
    db.add_line(5, p25, p35)
    db.add_line(5, p26, p36)
    db.add_line(5, p27, p37)
    db.add_line(5, p28, p38)
    db.add_line(5, p29, p39)
    db.add_line(5, p30, p40)

    db.add_line(4, p31, p32)
    db.add_line(4, p32, p33)
    db.add_line(4, p33, p34)
    db.add_line(4, p34, p35)
    db.add_line(4, p35, p36)
    db.add_line(4, p36, p37)
    db.add_line(4, p37, p38)
    db.add_line(4, p38, p39)
    db.add_line(4, p39, p40)

    db.add_line(5, p31, p41)
    db.add_line(5, p32, p42)
    db.add_line(5, p33, p43)
    db.add_line(5, p34, p44)
    db.add_line(5, p35, p45)
    db.add_line(5, p36, p46)
    db.add_line(5, p37, p47)
    db.add_line(5, p38, p48)
    db.add_line(5, p39, p49)
    db.add_line(5, p40, p50)


    db.add_line(4, p41, p42)
    db.add_line(4, p42, p43)
    db.add_line(4, p43, p44)
    db.add_line(4, p44, p45)
    db.add_line(4, p45, p46)
    db.add_line(4, p46, p47)
    db.add_line(4, p47, p48)
    db.add_line(4, p48, p49)
    db.add_line(4, p49, p50)

    db.add_line(5, p41, p51)
    db.add_line(5, p42, p52)
    db.add_line(5, p43, p53)
    db.add_line(5, p44, p54)
    db.add_line(5, p45, p55)
    db.add_line(5, p46, p56)
    db.add_line(5, p47, p57)
    db.add_line(5, p48, p58)
    db.add_line(5, p49, p59)
    db.add_line(5, p50, p60)


    db.add_line(4, p51, p52)
    db.add_line(4, p52, p53)
    db.add_line(4, p53, p54)
    db.add_line(4, p54, p55)
    db.add_line(4, p55, p56)
    db.add_line(4, p56, p57)
    db.add_line(4, p57, p58)
    db.add_line(4, p58, p59)
    db.add_line(4, p59, p60)

    db.add_line(5, p51, p61)
    db.add_line(5, p52, p62)
    db.add_line(5, p53, p63)
    db.add_line(5, p54, p64)
    db.add_line(5, p55, p65)
    db.add_line(5, p56, p66)
    db.add_line(5, p57, p67)
    db.add_line(5, p58, p68)
    db.add_line(5, p59, p69)
    db.add_line(5, p60, p70)


    db.add_line(4, p61, p62)
    db.add_line(4, p62, p63)
    db.add_line(4, p63, p64)
    db.add_line(4, p64, p65)
    db.add_line(4, p65, p66)
    db.add_line(4, p66, p67)
    db.add_line(4, p67, p68)
    db.add_line(4, p68, p69)
    db.add_line(4, p69, p70)

    db.add_line(5, p61, p71)
    db.add_line(5, p62, p72)
    db.add_line(5, p63, p73)
    db.add_line(5, p64, p74)
    db.add_line(5, p65, p75)
    db.add_line(5, p66, p76)
    db.add_line(5, p67, p77)
    db.add_line(5, p68, p78)
    db.add_line(5, p69, p79)
    db.add_line(5, p70, p80)


    db.add_line(4, p71, p72)
    db.add_line(4, p72, p73)
    db.add_line(4, p73, p74)
    db.add_line(4, p74, p75)
    db.add_line(4, p75, p76)
    db.add_line(4, p76, p77)
    db.add_line(4, p77, p78)
    db.add_line(4, p78, p79)
    db.add_line(4, p79, p80)

    db.add_line(5, p71, p81)
    db.add_line(5, p72, p82)
    db.add_line(5, p73, p83)
    db.add_line(5, p74, p84)
    db.add_line(5, p75, p85)
    db.add_line(5, p76, p86)
    db.add_line(5, p77, p87)
    db.add_line(5, p78, p88)
    db.add_line(5, p79, p89)
    db.add_line(5, p80, p90)


    db.add_line(4, p81, p82)
    db.add_line(4, p82, p83)
    db.add_line(4, p83, p84)
    db.add_line(4, p84, p85)
    db.add_line(4, p85, p86)
    db.add_line(4, p86, p87)
    db.add_line(4, p87, p88)
    db.add_line(4, p88, p89)
    db.add_line(4, p89, p90)

    db.add_line(5, p71, p81)
    db.add_line(5, p72, p82)
    db.add_line(5, p73, p83)
    db.add_line(5, p74, p84)
    db.add_line(5, p75, p85)
    db.add_line(5, p76, p86)
    db.add_line(5, p77, p87)
    db.add_line(5, p78, p88)
    db.add_line(5, p79, p89)
    db.add_line(5, p80, p90)


MAP_GENERATORS = {
    'map01': generate_map01,
    'map02': generate_map02,
    'map03': generate_map03
}

@task
def generate_map(ctx, map_name=None):
    """ Generation map.db
    """
    with DbMap() as db:
        if map_name is not None:
            if map_name not in MAP_GENERATORS:
                print("Error: Unknown map name:'{}'".format(map_name))
                raise InvFailure(1)
        db.reset_db()
        maps_to_generate = MAP_GENERATORS.keys() if map_name is None else [map_name, ]
        for curr_map in maps_to_generate:
            map_generator = MAP_GENERATORS[curr_map]
            map_generator(db)
            print("Map '{}' has been generated.".format(curr_map))
