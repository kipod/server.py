""" DB models.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from db.session import map_engine, replay_engine

MapBase = declarative_base(bind=map_engine)
ReplayBase = declarative_base(bind=replay_engine)


class Map(MapBase):

    __tablename__ = 'map'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    size_x = Column(Integer)
    size_y = Column(Integer)
    lines = relationship('Line', backref='map', lazy='dynamic')
    points = relationship('Point', backref='map', lazy='dynamic')
    posts = relationship('Post', backref='map', lazy='dynamic')

    def __repr__(self):
        return "<Map(id='{}', name='{}', size_x='{}', size_y='{}')>".format(
           self.id, self.name, self.size_x, self.size_y)


class Line(MapBase):

    __tablename__ = 'line'

    id = Column(Integer, primary_key=True)
    len = Column(Integer)
    p0 = Column(Integer)
    p1 = Column(Integer)
    map_id = Column(Integer, ForeignKey('map.id'))

    def __repr__(self):
        return "<Line(id='{}', len='{}', p0='{}', p1='{}', map_id='{}')>".format(
           self.id, self.len, self.p0, self.p1, self.map_id)


class Point(MapBase):

    __tablename__ = 'point'

    id = Column(Integer, primary_key=True)
    map_id = Column(Integer, ForeignKey('map.id'))
    x = Column(Integer)
    y = Column(Integer)
    posts = relationship('Post', backref='point', lazy='dynamic')

    def __repr__(self):
        return "<Point(id='{}', map_id='{}', x='{}', y='{}')>".format(
           self.id, self.map_id, self.x, self.y)


class Post(MapBase):

    __tablename__ = 'post'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(Integer)
    population = Column(Integer)
    armor = Column(Integer)
    product = Column(Integer)
    replenishment = Column(Integer)
    map_id = Column(Integer, ForeignKey('map.id'))
    point_id = Column(Integer, ForeignKey('point.id'))

    def __repr__(self):
        return (
            "<Post(id='{}', name='{}', type='{}', population='{}', armor='{}', "
            "product='{}', replenishment='{}', map_id='{}', point_id='{}')>".format(
                self.id, self.name, self.type, self.population, self.armor,
                self.product, self.replenishment, self.map_id, self.point_id
            )
        )


class Game(ReplayBase):

    __tablename__ = 'game'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    date = Column(DateTime)
    map_name = Column(String)
    actions = relationship('Action', backref='game', lazy='dynamic')
    num_players = Column(Integer)

    def __repr__(self):
        return "<Game(id='{}', name='{}', date='{}', map_name='{}', num_players='{}')>".format(
            self.id, self.name, self.date, self.map_name, self.num_players)


class Action(ReplayBase):

    __tablename__ = 'action'

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('game.id'))
    code = Column(Integer)
    message = Column(String)
    date = Column(DateTime)

    def __repr__(self):
        return "<Action(id='{}', game_id='{}', code='{}', message='{}', date='{}')>".format(
            self.id, self.game_id, self.code, self.message, self.date)
