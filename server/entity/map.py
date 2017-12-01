""" Game map entity.
"""
import json

from sqlalchemy import func

from db.models import Map as MapModel, Line as LineModel, Point as PointModel, Post as PostModel
from db.session import map_session_ctx
from entity.line import Line
from entity.point import Point
from entity.post import Post
from entity.serializable import Serializable
from entity.train import Train


class Map(Serializable):
    """ Map of game space.
    """
    def __init__(self, name=None):
        self.okey = False
        self.name = name
        self.idx = None
        self.size = (None, None)
        self.line = {}
        self.point = {}
        self.coordinate = {}
        self.post = {}
        self.train = {}

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
                    p.id, p.name, p.type, p.population, p.armor, p.product, replenishment=p.replenishment
                ) for p in posts}

        self.okey = True

    def add_train(self, train):
        self.train[train.idx] = train

    def from_json_str(self, string_data):
        data = json.loads(string_data)
        self.idx = data['idx']
        if 'name' in data:
            self.name = data['name']
        if 'size' in data:
            self.size = tuple(data['size'])
        if 'line' in data:
            self.line = {l['idx']: Line(l['idx'], l['length'], l['point'][0], l['point'][1]) for l in data['line']}
        if 'point' in data:
            self.point = {p['idx']: Point(p['idx'], post_id=p.get('post_id', None)) for p in data['point']}
        if 'post' in data:
            self.post = {
                p['idx']: Post(p['idx'], p['name'], p['type'], p.get('population', None), p.get('armor', None),
                               p.get('product', None), p.get('replenishment', None))
                for p in data['post']
            }
        if 'train' in data:
            self.train = {
                t['idx']: Train(t['idx'], t['line_idx'], t['position'], t['speed'], t['player_id'])
                for t in data['train']
            }
        if 'coordinate' in data:
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
