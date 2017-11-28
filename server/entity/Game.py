""" Game entity
"""
from threading import Thread, Event, Lock
from entity.Map import Map
from entity.Train import Train
from log import LOG
from defs import Result, Action
from entity.Post import Type as PostType
from db.replay import DbReplay

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

    TICK_TIME = 10

    # all registered games
    _map = {}

    def __init__(self, name, map_name='map02', observed=False):
        Thread.__init__(self, name=name)
        self.__replay = None
        self.__observed = observed
        if not observed:
            self.__replay = DbReplay()
        self.__lock = Lock()
        self.__current_game_id = 0
        self.__players = {}
        self.map = Map(map_name)
        self.name = name
        LOG(LOG.INFO, "Create game: %s", self.name)
        self.__trains = []
        self.__stop_event = Event()
        self.__pass_next_tick = False
        self.__next_train_move = {}
        if not observed:
            self.__current_game_id = self.__replay.add_game(name, map_name=self.map.name)
        self.market = [m for m in self.map.post.values() if m.type == PostType.MARKET]


    @staticmethod
    def create(name):
        """ returns instance of class Game
        """
        game = None
        if name in Game._map.keys():
            game = Game._map[name]
        else:
            game = Game(name)
            Game._map[name] = game
        return game


    def add_player(self, player):
        """ added player to the game
        """
        if not player.idx in self.__players:
            LOG(LOG.INFO, "Game: Add player [%s]", player.name)
            home = [point for point in self.map.point.values() if point.post_id is not None][0]
            player.set_home(home, level=self.map)
            train = Train(idx=len(self.__trains))
            player.add_train(train)
            self.__trains.append(train)
            self.map.add_train(train)
            line = [line for line in self.map.line.values()][0]
            train.line_idx = line.idx
            train.position = 0
            self.__players[player.idx] = player
            if not self.__observed:
                Thread.start(self)


    def turn(self):
        """ next turn
        """
        self.__pass_next_tick = True
        self.__lock.acquire()
        try:
            self.tick()
            if self.__replay:
                self.__replay.add_action(Action.TURN, None, with_commit=False)
        finally:
            self.__lock.release()


    def stop(self):
        """ stop ticks """
        LOG(LOG.INFO, "Game Stopped")
        self.__stop_event.set()
        if self.name in Game._map:
            del Game._map[self.name]
        if self.__replay:
            self.__replay.commit()


    def run(self):
        """
        Thread proc
        """
        replay = None
        if self.__replay:
            # create db connection object for this thread
            replay = DbReplay()
        try:
            while not self.__stop_event.wait(Game.TICK_TIME):
                self.__lock.acquire()
                try:
                    if self.__pass_next_tick:
                        self.__pass_next_tick = False
                    else:
                        self.tick()
                        if replay:
                            replay.add_action(Action.TURN,
                                              None,
                                              with_commit=False,
                                              game_id=self.__current_game_id)
                finally:
                    self.__lock.release()
            if replay:
                replay.commit()
        finally:
            if replay:
                replay.close()



    def tick(self):
        """ tick - update dynamic game entities """
        #LOG(LOG.INFO, "Game Tick")
        # update population and products in towns:
        for player_id in self.__players.keys():
            player = self.__players[player_id]
            if player.town.product > player.town.population:
                player.town.product -= player.town.population
            else:
                player.town.population -= 1
        # update all markets:
        for market in self.market:
            if market.product < market.product_capacity:
                market.product += 1
        for train in self.__trains:
            if train.line_idx in self.map.line:
                line = self.map.line[train.line_idx]
                if train.speed > 0:
                    if train.position < line.length:
                        train.position += 1
                    if train.position == line.length:
                        self.train_in_point(train, line.point[1])
                elif train.speed < 0:
                    if train.position > 0:
                        train.position -= 1
                    if train.position == 0:
                        self.train_in_point(train, line.point[0])
            else:
                LOG(LOG.ERROR, "Wrong train.line_idx: %d", train.line_idx)


    def train_in_point(self, train, point):
        """ the train arrived to point """
        LOG(LOG.INFO, "Train:%d arrive to point:%d pos:%d line:%d",
            train.idx, point, train.position, train.line_idx)

        post_id = self.map.point[point].post_id
        if post_id is not None:
            self.train_in_post(train, self.map.post[post_id])

        if train.idx in self.__next_train_move:
            next_move = self.__next_train_move[train.idx]
            if next_move["line_idx"] == train.line_idx: # if no next line
                if train.speed > 0 and train.position == self.map.line[train.line_idx].length:
                    train.speed = 0
                elif train.speed < 0 and train.position == 0:
                    train.speed = 0
            else:
                train.speed = next_move["speed"]
                train.line_idx = next_move["line_idx"]
                if train.speed > 0:
                    train.position = 0
                elif train.speed < 0:
                    train.position = self.map.line[train.line_idx].length
        else:
            train.speed = 0 # has not next move data


    def move_train(self, train_idx, speed, line_idx):
        """ process action MOVE """
        self.__lock.acquire()
        try:
            if train_idx >= len(self.__trains):
                return Result.RESOURCE_NOT_FOUND
            if train_idx in self.__next_train_move:
                del self.__next_train_move[train_idx]
            train = self.__trains[train_idx]
            player = self.__players[train.player_id]
            if line_idx not in self.map.line:
                return Result.RESOURCE_NOT_FOUND
            if speed == 0: # stop train!
                train.speed = speed
            elif train.speed == 0:
                if train.line_idx == line_idx: # continue run train
                    train.speed = speed
                elif self.map.line[train.line_idx].length == train.position:
                    line_from = self.map.line[train.line_idx]
                    line_to = self.map.line[line_idx]
                    if line_from.point[1] in line_to.point:
                        train.line_idx = line_idx
                        train.speed = speed
                        if line_from.point[1] == line_to.point[0]:
                            train.position = 0
                        else:
                            train.position = line_to.length
                elif train.position == 0:
                    line_from = self.map.line[train.line_idx]
                    line_to = self.map.line[line_idx]
                    if line_from.point[0] in line_to.point:
                        train.line_idx = line_idx
                        train.speed = speed
                        if line_from.point[0] == line_to.point[0]:
                            train.position = 0
                        else:
                            train.position = line_to.length

            elif train.speed != 0 and train.line_idx != line_idx: # train in moving
                switch_line_possible = False
                line_from = self.map.line[train.line_idx]
                line_to = self.map.line[line_idx]
                if train.speed > 0 and speed > 0:
                    switch_line_possible = (line_from.point[1] == line_to.point[0])
                elif train.speed > 0 and speed < 0:
                    switch_line_possible = (line_from.point[1] == line_to.point[1])
                elif train.speed < 0 and speed > 0:
                    switch_line_possible = (line_from.point[0] == line_to.point[0])
                elif train.speed < 0 and speed < 0:
                    switch_line_possible = (line_from.point[0] == line_to.point[1])
                if not switch_line_possible:
                    return Result.PATH_NOT_FOUND
                self.__next_train_move[train_idx] = {"speed": speed, "line_idx": line_idx}
        finally:
            self.__lock.release()
        return Result.OKEY


    def train_in_post(self, train, post):
        """ depends of post type train will be loaded or unloaded """
        if post.type == PostType.TOWN:
            # unload product from train to town
            post.product += train.product
            train.product = 0
        elif post.type == PostType.MARKET:
            # load product
            product = min(post.product, train.capacity)
            post.product -= product
            train.product += product

    def replay(self):
        """ obtain the replay object """
        return self.__replay
