""" Game map entity.
"""
import json

from sqlalchemy import func

from db.models import Map as MapModel, Line as LineModel, Point as PointModel, Post as PostModel
from db.session import map_session_ctx
from entity.line import Line
from entity.point import Point
from entity.post import Post, PostType
from entity.train import Train


class Map(object):
    """ Map of game space.
    """
    def __init__(self, name=None):
        self.name = name
        self.idx = None
        self.size = (None, None)
        self.line = {}
        self.point = {}
        self.coordinate = {}
        self.post = {}
        self.train = {}

        # Attributes not included into json representation:
        self.okey = False
        self.markets = []
        self.storages = []
        self.towns = []

        if self.name is not None:
            self.init_map()

    def init_map(self):
        with map_session_ctx() as session:
            _map = session.query(MapModel).filter(MapModel.name == self.name).first()
            self.idx = _map.id
            self.size = (_map.size_x, _map.size_y)

            lines = _map.lines.order_by(LineModel.id).all()
            self.line = {l.id: Line(l.id, l.len, l.p0, l.p1) for l in lines}

            points = session.query(PointModel, func.max(PostModel.id)).outerjoin(
                PostModel, PointModel.id == PostModel.point_id).filter(PointModel.map_id == _map.id).group_by(
                PointModel.id).order_by(PointModel.id).all()
            for point, post_id in points:
                self.coordinate[point.id] = {'idx': point.id, 'x': point.x, 'y': point.y}
                self.point[point.id] = Point(point.id, post_id=post_id)

            posts = _map.posts.order_by(PostModel.id).all()
            self.post = {
                p.id: Post(
                    p.id, p.name, p.type, p.population, p.armor, p.product,
                    replenishment=p.replenishment, point_id=p.point_id
                ) for p in posts
            }

            self.markets = [m for m in self.post.values() if m.type == PostType.MARKET]
            self.storages = [s for s in self.post.values() if s.type == PostType.STORAGE]
            self.towns = [t for t in self.post.values() if t.type == PostType.TOWN]

        self.okey = True

    def add_train(self, train):
        self.train[train.idx] = train

    def from_json_str(self, string_data):
        data = json.loads(string_data)
        if data.get('idx'):
            self.idx = data['idx']
        if data.get('name'):
            self.name = data['name']
        if data.get('size'):
            self.size = tuple(data['size'])
        if data.get('line'):
            self.line = {l['idx']: Line(l['idx'], l['length'], l['point'][0], l['point'][1]) for l in data['line']}
        if data.get('point'):
            self.point = {p['idx']: Point(p['idx'], post_id=p.get('post_id', None)) for p in data['point']}
        if data.get('post'):
            self.post = {
                p['idx']: Post(
                    p['idx'], p['name'], p['type'], population=p.get('population', None), armor=p.get('armor', None),
                    product=p.get('product', None), replenishment=p.get('replenishment', None),
                    level=p.get('level', None), player_id=p.get('player_id', None), point_id=p.get('point_id', None)
                )
                for p in data['post']
            }
        if data.get('train'):
            self.train = {
                t['idx']: Train(
                    t['idx'], line_idx=t['line_idx'], position=t['position'], speed=t['speed'],
                    player_id=t['player_id'], level=t['level'], goods=t['goods'], post_type=t['post_type']
                )
                for t in data['train']
            }
        if data.get('coordinate'):
            self.coordinate = {c['idx']: {'idx': c['idx'], 'x': c['x'], 'y': c['y']} for c in data['coordinate']}
        self.okey = True

    def layer_to_json_str(self, layer):
        data = {}
        choice_list = ()
        if layer == 0:
            choice_list = ('idx', 'name', 'point', 'line')
        elif layer == 1:
            choice_list = ('idx', 'post', 'train')
        elif layer == 10:
            choice_list = ('idx', 'size', 'coordinate')
        for key in self.__dict__:
            if key in choice_list:
                attribute = self.__dict__[key]
                if isinstance(attribute, dict):
                    data[key] = [i for i in attribute.values()]
                else:
                    data[key] = attribute
        return json.dumps(data, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def __repr__(self):
        return "<Map(idx={}, name={}, line_idx=[{}], point_idx=[{}], post_idx=[{}], train_idx=[{}])>".format(
            self.idx, self.name, ', '.join([str(k) for k in self.line]), ', '.join([str(k) for k in self.point]),
            ', '.join([str(k) for k in self.post]), ', '.join([str(k) for k in self.train])
        )
