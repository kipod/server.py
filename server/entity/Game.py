""" Game entity.
"""
from threading import Thread, Event, Lock

from db.replay import DbReplay
from defs import Result, Action
from entity.Map import Map
from entity.Post import PostType
from entity.Train import Train
from logger import log


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

    # All registered games.
    GAMES = {}

    def __init__(self, name, map_name='map02', observed=False):
        super(Game, self).__init__(name=name)
        log(log.INFO, "Create game: {}".format(self.name))
        self.replay = None
        self._observed = observed
        if not observed:
            self.replay = DbReplay()
        self._lock = Lock()
        self._current_game_id = 0
        self._players = {}
        self.map = Map(map_name)
        self.name = name
        self._trains = []
        self._stop_event = Event()
        self._pass_next_tick = False
        self._next_train_move = {}
        if not observed:
            self._current_game_id = self.replay.add_game(name, map_name=self.map.name)
        self.markets = [m for m in self.map.post.values() if m.type == PostType.MARKET]

    @staticmethod
    def create(name):
        """ Returns instance of class Game.
        """
        if name in Game.GAMES:
            game = Game.GAMES[name]
        else:
            Game.GAMES[name] = game = Game(name)
        return game

    def add_player(self, player):
        """ Adds player to the game.
        """
        if player.idx not in self._players:
            log(log.INFO, "Game: Add player '{}'".format(player.name))
            home = [point for point in self.map.point.values() if point.post_id is not None][0]
            player.set_home(home, level=self.map)
            train = Train(idx=len(self._trains))
            player.add_train(train)
            self._trains.append(train)
            self.map.add_train(train)
            line = [line for line in self.map.line.values()][0]
            train.line_idx = line.idx
            train.position = 0
            self._players[player.idx] = player
            if not self._observed:
                Thread.start(self)

    def turn(self):
        """ Makes next turn.
        """
        self._pass_next_tick = True
        with self._lock:
            self.tick()
            if self.replay:
                self.replay.add_action(Action.TURN, None, with_commit=False)

    def stop(self):
        """ Stops ticks.
        """
        log(log.INFO, "Game Stopped")
        self._stop_event.set()
        if self.name in Game.GAMES:
            del Game.GAMES[self.name]
        if self.replay:
            self.replay.commit()

    def run(self):
        """ Thread's activity.
        """
        # Create db connection object for this thread if replay.
        replay = DbReplay() if self.replay else None
        try:
            while not self._stop_event.wait(Game.TICK_TIME):
                with self._lock:
                    if self._pass_next_tick:
                        self._pass_next_tick = False
                    else:
                        self.tick()
                        if replay:
                            replay.add_action(Action.TURN, None, with_commit=False, game_id=self._current_game_id)
            if replay:
                replay.commit()
        finally:
            if replay:
                replay.close()

    def tick(self):
        """ Updates dynamic game entities.
        """
        # log(log.INFO, "Game Tick")
        # Update population and products in towns:
        for player in self._players.values():
            if player.town.product > player.town.population:
                player.town.product -= player.town.population
            else:
                player.town.population -= 1
        # Update all markets:
        for market in self.markets:
            if market.product < market.product_capacity:
                market.product += 1
        # Update trains positions:
        for train in self._trains:
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
                log(log.ERROR, "Wrong train.line_idx: {}".format(train.line_idx))

    def train_in_point(self, train, point):
        """ The train arrived to point.
        """
        log(log.INFO, "Train:{0} arrive to point:{1} pos:{2} line:{3}".format(
            train.idx, point, train.position, train.line_idx))

        post_id = self.map.point[point].post_id
        if post_id is not None:
            self.train_in_post(train, self.map.post[post_id])

        if train.idx in self._next_train_move:
            next_move = self._next_train_move[train.idx]
            if next_move['line_idx'] == train.line_idx:  # If no next line.
                if train.speed > 0 and train.position == self.map.line[train.line_idx].length:
                    train.speed = 0
                elif train.speed < 0 and train.position == 0:
                    train.speed = 0
            else:
                train.speed = next_move['speed']
                train.line_idx = next_move['line_idx']
                if train.speed > 0:
                    train.position = 0
                elif train.speed < 0:
                    train.position = self.map.line[train.line_idx].length
        else:
            train.speed = 0  # Has no next move data.

    def move_train(self, train_idx, speed, line_idx):
        """ Process action MOVE.
        """
        with self._lock:
            if train_idx >= len(self._trains):
                return Result.RESOURCE_NOT_FOUND
            if train_idx in self._next_train_move:
                del self._next_train_move[train_idx]
            train = self._trains[train_idx]
            if line_idx not in self.map.line:
                return Result.RESOURCE_NOT_FOUND
            if speed == 0:  # Stop train!
                train.speed = speed
            elif train.speed == 0:
                if train.line_idx == line_idx:  # Continue run train.
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

            elif train.speed != 0 and train.line_idx != line_idx:  # Train in moving.
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
                self._next_train_move[train_idx] = {'speed': speed, 'line_idx': line_idx}

        return Result.OKEY

    def train_in_post(self, train, post):
        """ Depends of post type train will be loaded or unloaded.
        """
        if post.type == PostType.TOWN:
            # Unload product from train to town
            post.product += train.product
            train.product = 0
        elif post.type == PostType.MARKET:
            # Load product from market to train.
            product = min(post.product, train.capacity)
            post.product -= product
            train.product += product
