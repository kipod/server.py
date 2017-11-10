""" Game entity
"""
from threading import Thread,Event
from entity.Map import Map
from entity.Player import Player
from entity.Train import Train
from log import LOG
from defs import Result
from entity.Post import Type as PostType

# all registered games
game_map = {}

class Game(Thread):
    """ game
        has:
          players - list of players on this game
          map - game map
          status - [ready, run, finish]
          tick_time - current time
          max_tick_time - time of game session
          name - unique game name
          trains - one train per player

    """
    def __init__(self, name):
        Thread.__init__(self, name=name)
        self.__players = {}
        self.map = Map('map01')
        self.name = name
        LOG(LOG.INFO, "Create game: %s", self.name)
        self.__trains = []
        self.__stop_event = Event()
        Thread.start(self)
        self.__pass_next_tick = False
        self.__next_train_move = {}


    @staticmethod
    def create(name):
        game = None
        if name in game_map.keys():
            game = game_map[name]
        else:
            game = Game(name)
            game_map[name] = game
        return game


    def add_player(self, player):
        if not player.idx in self.__players:
            LOG(LOG.INFO, "Game: Add player [%s]", player.name)
            player.set_home(self.map.point[1])
            train = Train(idx=len(self.__trains))
            player.add_train(train)
            self.__trains.append(train)
            self.map.add_train(train)
            self.__players[player.idx] = player


    def turn(self):
        self.__pass_next_tick = True
        self.tick()
        pass


    def stop(self):
        LOG(LOG.INFO, "Game Stopped")
        self.__stop_event.set()
        del game_map[self.name]


    def run(self):
        while not self.__stop_event.wait(1):
            if self.__pass_next_tick:
                self.__pass_next_tick = False
            else:
                self.tick()


    def tick(self):
        LOG(LOG.INFO, "Game Tick")
        for train in self.__trains:
            if train.line_idx in self.map.line:
                line = self.map.line[train.line_idx]
                if train.speed > 0:
                    if train.position < line.length:
                        train.position += 1
                    if train.position == line.length:
                        self.train_in_point(train, line.point[1])
                if train.speed < 0:
                    if train.position > 0:
                        train.position -= 1
                    if train.position == 0:
                        self.train_in_point(train, line.point[0])


    def train_in_point(self, train, point):
        LOG(LOG.INFO, "Train:%d arrive to point:%d pos:%d",
            train.idx, point, train.position)

        post_id = self.map.point[point].post_id
        if post_id is not None:
            self.train_in_post(train, self.map.post[post_id])

        if train.idx in self.__next_train_move:
            next_move = self.__next_train_move[train.idx]
            train.speed = next_move["speed"]
            train.line_idx = next_move["line_idx"]
            if train.speed > 0:
                train.position = 0
            elif train.speed < 0:
                train.position = self.map.line[train.line_idx].length
        else:
            train.speed = 0 # has not next move data


    def move_train(self, train_idx, speed, line_idx):
        train = self.__trains[train_idx]
        player = self.__players[train.player_id]
        if train.speed == 0: # initial move action
            train.speed = speed
            train.line_idx = line_idx
            line = self.map.line[line_idx]
            if line.point[0] == player.home.idx:
                train.position = 0
            elif line.point[1] == player.home.idx:
                train.position = line.length
            else:
                return Result.RESOURCE_NOT_FOUND
        else:
            if speed != 0:
                switch_line_possible = False
                line0 = self.map.line[train.line_idx]
                line1 = self.map.line[line_idx]
                if train.speed > 0 and speed > 0:
                    switch_line_possible = (line0.point[1] == line1.point[0])
                elif train.speed > 0 and speed < 0:
                    switch_line_possible = (line0.point[1] == line1.point[1])
                elif train.speed < 0 and speed > 0:
                    switch_line_possible = (line0.point[0] == line1.point[0])
                elif train.speed < 0 and speed < 0:
                    switch_line_possible = (line0.point[0] == line1.point[1])
                if not switch_line_possible:
                    return Result.PATH_NOT_FOUND
            self.__next_train_move[train_idx] = {"speed": speed, "line_idx": line_idx}
        return Result.OKEY


    def train_in_post(self, train, post):
        """ depends of post type train will be loaded or unloaded """
        if post.type == PostType.TOWN:
            # unload product from train to town
            post.product += train.product
            train.product = 0
        elif post.type == PostType.MARKET:
            # load product
            train.product += min(post.product, train.capacity)

