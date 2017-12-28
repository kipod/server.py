""" DB map generator.
"""
import sys
from functools import partial

from invoke import task

from db.models import MapBase, Map, Line, Point, Post
from db.session import MapSession, map_session_ctx
from entity.post import PostType
from game_config import CONFIG


def db_session(function):
    def wrapped(*args, **kwargs):
        if kwargs.get('session', None) is None:
            with map_session_ctx() as session:
                kwargs['session'] = session
                return function(*args, **kwargs)
        else:
            return function(*args, **kwargs)
    return wrapped


class DbMap(object):
    """ Contains helpers for map generation.
    """
    def __init__(self):
        self.current_map_id = None

    def reset_db(self):
        """ Re-applies DB schema.
        """
        MapBase.metadata.drop_all()
        MapBase.metadata.create_all()

    @db_session
    def add_map(self, size_x, size_y, name='', session=None):
        """ Creates new Map in DB.
        """
        new_map = Map(name=name, size_x=size_x, size_y=size_y)
        session.add(new_map)
        session.commit()  # Commit to get map's id.
        self.current_map_id = new_map.id
        return self.current_map_id

    @db_session
    def add_line(self, length, p0, p1, map_id=None, session=None):
        """ Creates new Line in DB.
        """
        _map_id = self.current_map_id if map_id is None else map_id
        new_line = Line(len=length, p0=p0, p1=p1, map_id=_map_id)
        session.add(new_line)
        session.commit()  # Commit to get line's id.
        return new_line.id

    @db_session
    def add_point(self, map_id=None, x=0, y=0, session=None):
        """ Creates new Point in DB.
        """
        _map_id = self.current_map_id if map_id is None else map_id
        new_point = Point(map_id=_map_id, x=x, y=y)
        session.add(new_point)
        session.commit()  # Commit to get point's id.
        return new_point.id

    @db_session
    def add_post(self, point_id, name, type_p, population=0, armor=0, product=0, replenishment=1, map_id=None,
                 session=None):
        """ Creates new Post in DB.
        """
        _map_id = self.current_map_id if map_id is None else map_id
        new_post = Post(name=name, type=type_p, population=population, armor=armor, product=product,
                        replenishment=replenishment, map_id=_map_id, point_id=point_id)
        session.add(new_post)
        session.commit()  # Commit to get post's id.
        return new_post.id


def generate_map01(db: DbMap, session: MapSession):
    """ Generates 'map01'. See 'map01.png'.
    """
    # Map:
    db.add_map(name=CONFIG.MAP_NAME, size_x=330, size_y=248, session=session)
    add_point = partial(db.add_point, session=session)
    add_post = partial(db.add_post, session=session)
    add_line = partial(db.add_line, session=session)

    # Points:
    p1 = add_point(x=75, y=16)
    p2 = add_point(x=250, y=16)
    p3 = add_point(x=312, y=120)
    p4 = add_point(x=250, y=220)
    p5 = add_point(x=100, y=220)
    p6 = add_point(x=10, y=120)
    p7 = add_point(x=134, y=70)
    p8 = add_point(x=200, y=70)
    p9 = add_point(x=235, y=120)
    p10 = add_point(x=198, y=160)
    p11 = add_point(x=134, y=160)
    p12 = add_point(x=85, y=120)

    # Posts:
    add_post(p1, 'town-one', PostType.TOWN, population=10)
    add_post(p7, 'market-one', PostType.MARKET, product=20, replenishment=1)

    # Lines:
    add_line(10, p1, p7)  # 1: 1-7
    add_line(10, p8, p2)  # 2: 8-2
    add_line(10, p9, p3)  # 3: 9-3
    add_line(10, p10, p4)  # 4: 10-4
    add_line(10, p11, p5)  # 5: 11-5
    add_line(10, p12, p6)  # 6: 12-6
    add_line(10, p7, p8)  # 7: 7-8
    add_line(10, p8, p9)  # 8: 8-9
    add_line(10, p9, p10)  # 9: 9-10
    add_line(10, p10, p11)  # 10: 10-11
    add_line(10, p11, p12)  # 11: 11-12
    add_line(10, p12, p7)  # 12: 12-7


def generate_map02(db: DbMap, session: MapSession):
    """ Generates 'map02'. See 'map02.png'. This map is used for tests.
    """
    # Map:
    db.add_map(name=CONFIG.MAP_NAME, size_x=330, size_y=248, session=session)
    add_point = partial(db.add_point, session=session)
    add_post = partial(db.add_post, session=session)
    add_line = partial(db.add_line, session=session)

    # Points:
    p1 = add_point(x=75, y=16)
    p2 = add_point(x=250, y=16)
    p3 = add_point(x=312, y=120)
    p4 = add_point(x=250, y=220)
    p5 = add_point(x=100, y=220)
    p6 = add_point(x=10, y=120)
    p7 = add_point(x=134, y=70)
    p8 = add_point(x=200, y=70)
    p9 = add_point(x=235, y=120)
    p10 = add_point(x=198, y=160)
    p11 = add_point(x=134, y=160)
    p12 = add_point(x=85, y=120)

    # Posts:
    add_post(p1, 'town-one', PostType.TOWN, population=3, product=60, armor=3)
    add_post(p3, 'town-two', PostType.TOWN, population=3, product=60, armor=3)
    add_post(p4, 'market-big', PostType.MARKET, product=36, replenishment=2)
    add_post(p5, 'market-medium', PostType.MARKET, product=28, replenishment=1)
    add_post(p7, 'market-small', PostType.MARKET, product=5, replenishment=1)
    add_post(p6, 'storage-big', PostType.STORAGE, armor=48, replenishment=2)

    # Lines:
    add_line(1, p1, p7)  # 1: 1-7
    add_line(1, p8, p2)  # 2: 8-2
    add_line(1, p9, p3)  # 3: 9-3
    add_line(1, p10, p4)  # 4: 10-4
    add_line(1, p11, p5)  # 5: 11-5
    add_line(2, p12, p6)  # 6: 12-6
    add_line(1, p7, p8)  # 7: 7-8
    add_line(2, p8, p9)  # 8: 8-9
    add_line(2, p9, p10)  # 9: 9-10
    add_line(1, p10, p11)  # 10: 10-11
    add_line(3, p11, p12)  # 11: 11-12
    add_line(1, p12, p7)  # 12: 12-7
    add_line(2, p1, p2)  # 13: 1-2
    add_line(2, p2, p3)  # 14: 2-3
    add_line(1, p3, p4)  # 15: 3-4
    add_line(3, p4, p5)  # 16: 4-5
    add_line(1, p5, p6)  # 17: 5-6
    add_line(3, p6, p1)  # 18: 6-1


def generate_map03(db: DbMap, session: MapSession):
    """ Generates 'map03'. See 'map03.png'.
    """
    # Map:
    db.add_map(name=CONFIG.MAP_NAME, size_x=200, size_y=200, session=session)
    add_point = partial(db.add_point, session=session)
    add_post = partial(db.add_post, session=session)
    add_line = partial(db.add_line, session=session)

    # Points:
    p1 = add_point(x=10, y=10)
    p2 = add_point(x=30, y=10)
    p3 = add_point(x=50, y=10)
    p4 = add_point(x=70, y=10)
    p5 = add_point(x=90, y=10)
    p6 = add_point(x=110, y=10)
    p7 = add_point(x=130, y=10)
    p8 = add_point(x=150, y=10)
    p9 = add_point(x=170, y=10)
    p10 = add_point(x=190, y=10)

    p11 = add_point(x=10, y=30)
    p12 = add_point(x=30, y=30)
    p13 = add_point(x=50, y=30)
    p14 = add_point(x=70, y=30)
    p15 = add_point(x=90, y=30)
    p16 = add_point(x=110, y=30)
    p17 = add_point(x=130, y=30)
    p18 = add_point(x=150, y=30)
    p19 = add_point(x=170, y=30)
    p20 = add_point(x=190, y=30)

    p21 = add_point(x=10, y=50)
    p22 = add_point(x=30, y=50)
    p23 = add_point(x=50, y=50)
    p24 = add_point(x=70, y=50)
    p25 = add_point(x=90, y=50)
    p26 = add_point(x=110, y=50)
    p27 = add_point(x=130, y=50)
    p28 = add_point(x=150, y=50)
    p29 = add_point(x=170, y=50)
    p30 = add_point(x=190, y=50)

    p31 = add_point(x=10, y=70)
    p32 = add_point(x=30, y=70)
    p33 = add_point(x=50, y=70)
    p34 = add_point(x=70, y=70)
    p35 = add_point(x=90, y=70)
    p36 = add_point(x=110, y=70)
    p37 = add_point(x=130, y=70)
    p38 = add_point(x=150, y=70)
    p39 = add_point(x=170, y=70)
    p40 = add_point(x=190, y=70)

    p41 = add_point(x=10, y=90)
    p42 = add_point(x=30, y=90)
    p43 = add_point(x=50, y=90)
    p44 = add_point(x=70, y=90)
    p45 = add_point(x=90, y=90)
    p46 = add_point(x=110, y=90)
    p47 = add_point(x=130, y=90)
    p48 = add_point(x=150, y=90)
    p49 = add_point(x=170, y=90)
    p50 = add_point(x=190, y=90)

    p51 = add_point(x=10, y=110)
    p52 = add_point(x=30, y=110)
    p53 = add_point(x=50, y=110)
    p54 = add_point(x=70, y=110)
    p55 = add_point(x=90, y=110)
    p56 = add_point(x=110, y=110)
    p57 = add_point(x=130, y=110)
    p58 = add_point(x=150, y=110)
    p59 = add_point(x=170, y=110)
    p60 = add_point(x=190, y=110)

    p61 = add_point(x=10, y=130)
    p62 = add_point(x=30, y=130)
    p63 = add_point(x=50, y=130)
    p64 = add_point(x=70, y=130)
    p65 = add_point(x=90, y=130)
    p66 = add_point(x=110, y=130)
    p67 = add_point(x=130, y=130)
    p68 = add_point(x=150, y=130)
    p69 = add_point(x=170, y=130)
    p70 = add_point(x=190, y=130)

    p71 = add_point(x=10, y=150)
    p72 = add_point(x=30, y=150)
    p73 = add_point(x=50, y=150)
    p74 = add_point(x=70, y=150)
    p75 = add_point(x=90, y=150)
    p76 = add_point(x=110, y=150)
    p77 = add_point(x=130, y=150)
    p78 = add_point(x=150, y=150)
    p79 = add_point(x=170, y=150)
    p80 = add_point(x=190, y=150)

    p81 = add_point(x=10, y=170)
    p82 = add_point(x=30, y=170)
    p83 = add_point(x=50, y=170)
    p84 = add_point(x=70, y=170)
    p85 = add_point(x=90, y=170)
    p86 = add_point(x=110, y=170)
    p87 = add_point(x=130, y=170)
    p88 = add_point(x=150, y=170)
    p89 = add_point(x=170, y=170)
    p90 = add_point(x=190, y=170)

    p91 = add_point(x=10, y=190)
    p92 = add_point(x=30, y=190)
    p93 = add_point(x=50, y=190)
    p94 = add_point(x=70, y=190)
    p95 = add_point(x=90, y=190)
    p96 = add_point(x=110, y=190)
    p97 = add_point(x=130, y=190)
    p98 = add_point(x=150, y=190)
    p99 = add_point(x=170, y=190)
    p100 = add_point(x=190, y=190)

    # Posts:
    add_post(p1, 'town-one', PostType.TOWN, population=3, product=200, armor=100)
    add_post(p89, 'market-big', PostType.MARKET, product=500, replenishment=10)
    add_post(p49, 'market-medium', PostType.MARKET, product=250, replenishment=10)
    add_post(p12, 'market-small', PostType.MARKET, product=50, replenishment=5)
    add_post(p32, 'storage-small', PostType.STORAGE, armor=20, replenishment=1)
    add_post(p56, 'storage-big', PostType.STORAGE, armor=100, replenishment=5)

    # Lines:
    add_line(4, p1, p2)
    add_line(4, p2, p3)
    add_line(4, p3, p4)
    add_line(4, p4, p5)
    add_line(4, p5, p6)
    add_line(4, p6, p7)
    add_line(4, p7, p8)
    add_line(4, p8, p9)
    add_line(4, p9, p10)

    add_line(5, p1, p11)
    add_line(5, p2, p12)
    add_line(5, p3, p13)
    add_line(5, p4, p14)
    add_line(5, p5, p15)
    add_line(5, p6, p16)
    add_line(5, p7, p17)
    add_line(5, p8, p18)
    add_line(5, p9, p19)
    add_line(5, p10, p20)


    add_line(4, p11, p12)  # noqa E303
    add_line(4, p12, p13)
    add_line(4, p13, p14)
    add_line(4, p14, p15)
    add_line(4, p15, p16)
    add_line(4, p16, p17)
    add_line(4, p17, p18)
    add_line(4, p18, p19)
    add_line(4, p19, p20)

    add_line(5, p11, p21)
    add_line(5, p12, p22)
    add_line(5, p13, p23)
    add_line(5, p14, p24)
    add_line(5, p15, p25)
    add_line(5, p16, p26)
    add_line(5, p17, p27)
    add_line(5, p18, p28)
    add_line(5, p19, p29)
    add_line(5, p20, p30)


    add_line(4, p21, p22)  # noqa E303
    add_line(4, p22, p23)
    add_line(4, p23, p24)
    add_line(4, p24, p25)
    add_line(4, p25, p26)
    add_line(4, p26, p27)
    add_line(4, p27, p28)
    add_line(4, p28, p29)
    add_line(4, p29, p30)

    add_line(5, p21, p31)
    add_line(5, p22, p32)
    add_line(5, p23, p33)
    add_line(5, p24, p34)
    add_line(5, p25, p35)
    add_line(5, p26, p36)
    add_line(5, p27, p37)
    add_line(5, p28, p38)
    add_line(5, p29, p39)
    add_line(5, p30, p40)

    add_line(4, p31, p32)
    add_line(4, p32, p33)
    add_line(4, p33, p34)
    add_line(4, p34, p35)
    add_line(4, p35, p36)
    add_line(4, p36, p37)
    add_line(4, p37, p38)
    add_line(4, p38, p39)
    add_line(4, p39, p40)

    add_line(5, p31, p41)
    add_line(5, p32, p42)
    add_line(5, p33, p43)
    add_line(5, p34, p44)
    add_line(5, p35, p45)
    add_line(5, p36, p46)
    add_line(5, p37, p47)
    add_line(5, p38, p48)
    add_line(5, p39, p49)
    add_line(5, p40, p50)


    add_line(4, p41, p42)  # noqa E303
    add_line(4, p42, p43)
    add_line(4, p43, p44)
    add_line(4, p44, p45)
    add_line(4, p45, p46)
    add_line(4, p46, p47)
    add_line(4, p47, p48)
    add_line(4, p48, p49)
    add_line(4, p49, p50)

    add_line(5, p41, p51)
    add_line(5, p42, p52)
    add_line(5, p43, p53)
    add_line(5, p44, p54)
    add_line(5, p45, p55)
    add_line(5, p46, p56)
    add_line(5, p47, p57)
    add_line(5, p48, p58)
    add_line(5, p49, p59)
    add_line(5, p50, p60)


    add_line(4, p51, p52)  # noqa E303
    add_line(4, p52, p53)
    add_line(4, p53, p54)
    add_line(4, p54, p55)
    add_line(4, p55, p56)
    add_line(4, p56, p57)
    add_line(4, p57, p58)
    add_line(4, p58, p59)
    add_line(4, p59, p60)

    add_line(5, p51, p61)
    add_line(5, p52, p62)
    add_line(5, p53, p63)
    add_line(5, p54, p64)
    add_line(5, p55, p65)
    add_line(5, p56, p66)
    add_line(5, p57, p67)
    add_line(5, p58, p68)
    add_line(5, p59, p69)
    add_line(5, p60, p70)


    add_line(4, p61, p62)  # noqa E303
    add_line(4, p62, p63)
    add_line(4, p63, p64)
    add_line(4, p64, p65)
    add_line(4, p65, p66)
    add_line(4, p66, p67)
    add_line(4, p67, p68)
    add_line(4, p68, p69)
    add_line(4, p69, p70)

    add_line(5, p61, p71)
    add_line(5, p62, p72)
    add_line(5, p63, p73)
    add_line(5, p64, p74)
    add_line(5, p65, p75)
    add_line(5, p66, p76)
    add_line(5, p67, p77)
    add_line(5, p68, p78)
    add_line(5, p69, p79)
    add_line(5, p70, p80)


    add_line(4, p71, p72)  # noqa E303
    add_line(4, p72, p73)
    add_line(4, p73, p74)
    add_line(4, p74, p75)
    add_line(4, p75, p76)
    add_line(4, p76, p77)
    add_line(4, p77, p78)
    add_line(4, p78, p79)
    add_line(4, p79, p80)

    add_line(5, p71, p81)
    add_line(5, p72, p82)
    add_line(5, p73, p83)
    add_line(5, p74, p84)
    add_line(5, p75, p85)
    add_line(5, p76, p86)
    add_line(5, p77, p87)
    add_line(5, p78, p88)
    add_line(5, p79, p89)
    add_line(5, p80, p90)


    add_line(4, p81, p82)  # noqa E303
    add_line(4, p82, p83)
    add_line(4, p83, p84)
    add_line(4, p84, p85)
    add_line(4, p85, p86)
    add_line(4, p86, p87)
    add_line(4, p87, p88)
    add_line(4, p88, p89)
    add_line(4, p89, p90)

    add_line(5, p81, p91)
    add_line(5, p82, p92)
    add_line(5, p83, p93)
    add_line(5, p84, p94)
    add_line(5, p85, p95)
    add_line(5, p86, p96)
    add_line(5, p87, p97)
    add_line(5, p88, p98)
    add_line(5, p89, p99)
    add_line(5, p90, p100)


    add_line(4, p91, p92)  # noqa E303
    add_line(4, p92, p93)
    add_line(4, p93, p94)
    add_line(4, p94, p95)
    add_line(4, p95, p96)
    add_line(4, p96, p97)
    add_line(4, p97, p98)
    add_line(4, p98, p99)
    add_line(4, p99, p100)


def generate_map04(db: DbMap, session: MapSession):
    """ Generates 'map04'. See 'map04.png'.
    """
    # Map:
    db.add_map(name=CONFIG.MAP_NAME, size_x=200, size_y=200, session=session)
    add_point = partial(db.add_point, session=session)
    add_post = partial(db.add_post, session=session)
    add_line = partial(db.add_line, session=session)

    # Points:
    p1 = add_point(x=10, y=10)
    p2 = add_point(x=30, y=10)
    p3 = add_point(x=50, y=10)
    p4 = add_point(x=70, y=10)
    p5 = add_point(x=90, y=10)
    p6 = add_point(x=110, y=10)
    p7 = add_point(x=130, y=10)
    p8 = add_point(x=150, y=10)
    p9 = add_point(x=170, y=10)
    p10 = add_point(x=190, y=10)

    p11 = add_point(x=10, y=30)
    p12 = add_point(x=30, y=30)
    p13 = add_point(x=50, y=30)
    p14 = add_point(x=70, y=30)
    p15 = add_point(x=90, y=30)
    p16 = add_point(x=110, y=30)
    p17 = add_point(x=130, y=30)
    p18 = add_point(x=150, y=30)
    p19 = add_point(x=170, y=30)
    p20 = add_point(x=190, y=30)

    p21 = add_point(x=10, y=50)
    p22 = add_point(x=30, y=50)
    p23 = add_point(x=50, y=50)
    p24 = add_point(x=70, y=50)
    p25 = add_point(x=90, y=50)
    p26 = add_point(x=110, y=50)
    p27 = add_point(x=130, y=50)
    p28 = add_point(x=150, y=50)
    p29 = add_point(x=170, y=50)
    p30 = add_point(x=190, y=50)

    p31 = add_point(x=10, y=70)
    p32 = add_point(x=30, y=70)
    p33 = add_point(x=50, y=70)
    p34 = add_point(x=70, y=70)
    p35 = add_point(x=90, y=70)
    p36 = add_point(x=110, y=70)
    p37 = add_point(x=130, y=70)
    p38 = add_point(x=150, y=70)
    p39 = add_point(x=170, y=70)
    p40 = add_point(x=190, y=70)

    p41 = add_point(x=10, y=90)
    p42 = add_point(x=30, y=90)
    p43 = add_point(x=50, y=90)
    p44 = add_point(x=70, y=90)
    p45 = add_point(x=90, y=90)
    p46 = add_point(x=110, y=90)
    p47 = add_point(x=130, y=90)
    p48 = add_point(x=150, y=90)
    p49 = add_point(x=170, y=90)
    p50 = add_point(x=190, y=90)

    p51 = add_point(x=10, y=110)
    p52 = add_point(x=30, y=110)
    p53 = add_point(x=50, y=110)
    p54 = add_point(x=70, y=110)
    p55 = add_point(x=90, y=110)
    p56 = add_point(x=110, y=110)
    p57 = add_point(x=130, y=110)
    p58 = add_point(x=150, y=110)
    p59 = add_point(x=170, y=110)
    p60 = add_point(x=190, y=110)

    p61 = add_point(x=10, y=130)
    p62 = add_point(x=30, y=130)
    p63 = add_point(x=50, y=130)
    p64 = add_point(x=70, y=130)
    p65 = add_point(x=90, y=130)
    p66 = add_point(x=110, y=130)
    p67 = add_point(x=130, y=130)
    p68 = add_point(x=150, y=130)
    p69 = add_point(x=170, y=130)
    p70 = add_point(x=190, y=130)

    p71 = add_point(x=10, y=150)
    p72 = add_point(x=30, y=150)
    p73 = add_point(x=50, y=150)
    p74 = add_point(x=70, y=150)
    p75 = add_point(x=90, y=150)
    p76 = add_point(x=110, y=150)
    p77 = add_point(x=130, y=150)
    p78 = add_point(x=150, y=150)
    p79 = add_point(x=170, y=150)
    p80 = add_point(x=190, y=150)

    p81 = add_point(x=10, y=170)
    p82 = add_point(x=30, y=170)
    p83 = add_point(x=50, y=170)
    p84 = add_point(x=70, y=170)
    p85 = add_point(x=90, y=170)
    p86 = add_point(x=110, y=170)
    p87 = add_point(x=130, y=170)
    p88 = add_point(x=150, y=170)
    p89 = add_point(x=170, y=170)
    p90 = add_point(x=190, y=170)

    p91 = add_point(x=10, y=190)
    p92 = add_point(x=30, y=190)
    p93 = add_point(x=50, y=190)
    p94 = add_point(x=70, y=190)
    p95 = add_point(x=90, y=190)
    p96 = add_point(x=110, y=190)
    p97 = add_point(x=130, y=190)
    p98 = add_point(x=150, y=190)
    p99 = add_point(x=170, y=190)
    p100 = add_point(x=190, y=190)

    # Posts:
    # Towns:
    add_post(p1, 'Kiev', PostType.TOWN, population=1, product=200, armor=100)
    add_post(p10, 'Minsk', PostType.TOWN, population=1, product=200, armor=100)
    add_post(p91, 'Saint Petersburg', PostType.TOWN, population=1, product=200, armor=100)
    add_post(p100, 'Tallinn', PostType.TOWN, population=1, product=200, armor=100)
    # Markets:
    add_post(p34, 'market-01', PostType.MARKET, product=500, replenishment=10)
    add_post(p37, 'market-02', PostType.MARKET, product=500, replenishment=10)
    add_post(p64, 'market-03', PostType.MARKET, product=500, replenishment=10)
    add_post(p67, 'market-04', PostType.MARKET, product=500, replenishment=10)
    # Storages:
    add_post(p45, 'storage-01', PostType.STORAGE, armor=20, replenishment=5)
    add_post(p46, 'storage-02', PostType.STORAGE, armor=20, replenishment=5)
    add_post(p55, 'storage-03', PostType.STORAGE, armor=20, replenishment=5)
    add_post(p56, 'storage-04', PostType.STORAGE, armor=20, replenishment=5)

    # Lines:
    add_line(4, p1, p2)  # 1
    add_line(4, p2, p3)  # 2
    add_line(4, p3, p4)  # 3
    add_line(4, p4, p5)  # 4
    add_line(4, p5, p6)  # 5
    add_line(4, p6, p7)  # 6
    add_line(4, p7, p8)  # 7
    add_line(4, p8, p9)  # 8
    add_line(4, p9, p10)  # 9

    add_line(5, p1, p11)  # 10
    add_line(5, p2, p12)  # 11
    add_line(5, p3, p13)  # 12
    add_line(5, p4, p14)  # 13
    add_line(5, p5, p15)  # 14
    add_line(5, p6, p16)  # 15
    add_line(5, p7, p17)  # 16
    add_line(5, p8, p18)  # 17
    add_line(5, p9, p19)  # 18
    add_line(5, p10, p20)  # 19

    add_line(4, p11, p12)  # 20
    add_line(4, p12, p13)  # 21
    add_line(4, p13, p14)  # 22
    add_line(4, p14, p15)  # 23
    add_line(4, p15, p16)  # 24
    add_line(4, p16, p17)  # 25
    add_line(4, p17, p18)  # 26
    add_line(4, p18, p19)  # 27
    add_line(4, p19, p20)  # 28

    add_line(5, p11, p21)  # 29
    add_line(5, p12, p22)  # 30
    add_line(5, p13, p23)  # 31
    add_line(5, p14, p24)  # 32
    add_line(5, p15, p25)  # 33
    add_line(5, p16, p26)  # 34
    add_line(5, p17, p27)  # 35
    add_line(5, p18, p28)  # 36
    add_line(5, p19, p29)  # 37
    add_line(5, p20, p30)  # 38

    add_line(4, p21, p22)  # 39
    add_line(4, p22, p23)  # 40
    add_line(4, p23, p24)  # 41
    add_line(4, p24, p25)  # 42
    add_line(4, p25, p26)  # 43
    add_line(4, p26, p27)  # 44
    add_line(4, p27, p28)  # 45
    add_line(4, p28, p29)  # 46
    add_line(4, p29, p30)  # 47

    add_line(5, p21, p31)  # 48
    add_line(5, p22, p32)  # 49
    add_line(5, p23, p33)  # 50
    add_line(5, p24, p34)  # 51
    add_line(5, p25, p35)  # 52
    add_line(5, p26, p36)  # 53
    add_line(5, p27, p37)  # 54
    add_line(5, p28, p38)  # 55
    add_line(5, p29, p39)  # 56
    add_line(5, p30, p40)  # 57

    add_line(4, p31, p32)  # 58
    add_line(4, p32, p33)  # 59
    add_line(4, p33, p34)  # 60
    add_line(4, p34, p35)  # 61
    add_line(4, p35, p36)  # 62
    add_line(4, p36, p37)  # 63
    add_line(4, p37, p38)  # 64
    add_line(4, p38, p39)  # 65
    add_line(4, p39, p40)  # 66

    add_line(5, p31, p41)  # 67
    add_line(5, p32, p42)  # 68
    add_line(5, p33, p43)  # 69
    add_line(5, p34, p44)  # 70
    add_line(5, p35, p45)  # 71
    add_line(5, p36, p46)  # 72
    add_line(5, p37, p47)  # 73
    add_line(5, p38, p48)  # 74
    add_line(5, p39, p49)  # 75
    add_line(5, p40, p50)  # 76


    add_line(4, p41, p42)  # 77 # noqa E303
    add_line(4, p42, p43)  # 78
    add_line(4, p43, p44)  # 79
    add_line(4, p44, p45)  # 80
    add_line(2, p45, p46)  # 81
    add_line(4, p46, p47)  # 82
    add_line(4, p47, p48)  # 83
    add_line(4, p48, p49)  # 84
    add_line(4, p49, p50)  # 85

    add_line(5, p41, p51)  # 86
    add_line(5, p42, p52)  # 87
    add_line(5, p43, p53)  # 88
    add_line(5, p44, p54)  # 89
    add_line(2, p45, p55)  # 90
    add_line(2, p46, p56)  # 91
    add_line(5, p47, p57)  # 92
    add_line(5, p48, p58)  # 93
    add_line(5, p49, p59)  # 94
    add_line(5, p50, p60)  # 95


    add_line(4, p51, p52)  # noqa E303
    add_line(4, p52, p53)
    add_line(4, p53, p54)
    add_line(4, p54, p55)
    add_line(2, p55, p56)
    add_line(4, p56, p57)
    add_line(4, p57, p58)
    add_line(4, p58, p59)
    add_line(4, p59, p60)

    add_line(5, p51, p61)
    add_line(5, p52, p62)
    add_line(5, p53, p63)
    add_line(5, p54, p64)
    add_line(5, p55, p65)
    add_line(5, p56, p66)
    add_line(5, p57, p67)
    add_line(5, p58, p68)
    add_line(5, p59, p69)
    add_line(5, p60, p70)


    add_line(4, p61, p62)  # noqa E303
    add_line(4, p62, p63)
    add_line(4, p63, p64)
    add_line(4, p64, p65)
    add_line(4, p65, p66)
    add_line(4, p66, p67)
    add_line(4, p67, p68)
    add_line(4, p68, p69)
    add_line(4, p69, p70)

    add_line(5, p61, p71)
    add_line(5, p62, p72)
    add_line(5, p63, p73)
    add_line(5, p64, p74)
    add_line(5, p65, p75)
    add_line(5, p66, p76)
    add_line(5, p67, p77)
    add_line(5, p68, p78)
    add_line(5, p69, p79)
    add_line(5, p70, p80)


    add_line(4, p71, p72)  # noqa E303
    add_line(4, p72, p73)
    add_line(4, p73, p74)
    add_line(4, p74, p75)
    add_line(4, p75, p76)
    add_line(4, p76, p77)
    add_line(4, p77, p78)
    add_line(4, p78, p79)
    add_line(4, p79, p80)

    add_line(5, p71, p81)
    add_line(5, p72, p82)
    add_line(5, p73, p83)
    add_line(5, p74, p84)
    add_line(5, p75, p85)
    add_line(5, p76, p86)
    add_line(5, p77, p87)
    add_line(5, p78, p88)
    add_line(5, p79, p89)
    add_line(5, p80, p90)


    add_line(4, p81, p82)  # noqa E303
    add_line(4, p82, p83)
    add_line(4, p83, p84)
    add_line(4, p84, p85)
    add_line(4, p85, p86)
    add_line(4, p86, p87)
    add_line(4, p87, p88)
    add_line(4, p88, p89)
    add_line(4, p89, p90)

    add_line(5, p81, p91)
    add_line(5, p82, p92)
    add_line(5, p83, p93)
    add_line(5, p84, p94)
    add_line(5, p85, p95)
    add_line(5, p86, p96)
    add_line(5, p87, p97)
    add_line(5, p88, p98)
    add_line(5, p89, p99)
    add_line(5, p90, p100)


    add_line(4, p91, p92)  # noqa E303
    add_line(4, p92, p93)
    add_line(4, p93, p94)
    add_line(4, p94, p95)
    add_line(4, p95, p96)
    add_line(4, p96, p97)
    add_line(4, p97, p98)
    add_line(4, p98, p99)
    add_line(4, p99, p100)


MAP_GENERATORS = {
    'map01': generate_map01,
    'map02': generate_map02,
    'map03': generate_map03,
    'map04': generate_map04,
}


@task
def generate_map(_, map_version=CONFIG.CURRENT_MAP_VERSION):
    """ Generates 'map.db'.
    """
    if map_version is not None and map_version not in MAP_GENERATORS:
        print("Error, unknown map name: '{}', available: {}".format(
            map_version, ', '.join(MAP_GENERATORS.keys())))
        sys.exit(1)
    database = DbMap()
    database.reset_db()
    maps_to_generate = MAP_GENERATORS.keys() if map_version is None else [map_version, ]
    with map_session_ctx() as session:
        for curr_map in maps_to_generate:
            map_generator = MAP_GENERATORS[curr_map]
            map_generator(database, session)
            print("Map '{}' has been generated.".format(curr_map))
    sys.exit(0)
