""" Game entity.
"""
import random
from threading import Thread, Event, Lock

import game_config
from db.replay import DbReplay
from defs import Result, Action
from entity.map import Map
from entity.post import PostType
from entity.train import Train
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

    # All registered games.
    GAMES = {}

    def __init__(self, name, map_name=game_config.MAP_NAME, observed=False):
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
        self._trains = {}
        self._stop_event = Event()
        self._pass_next_tick = False
        self._next_train_moves = {}
        if not observed:
            self._current_game_id = self.replay.add_game(name, map_name=self.map.name)
        random.seed()

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
            # Use first Town on the map as player's Town:
            player_town = self.map.towns[0]
            player_home_point = self.map.point[player_town.point_id]
            player.set_home(player_home_point, player_town)
            # Add trains for the player:
            for _ in range(game_config.DEFAULT_TRAINS_COUNT):
                # Create Train:
                train = Train(idx=len(self._trains) + 1)
                # Use first Line connected to the Town as default train's line:
                line = [line for line in self.map.line.values() if player_home_point.idx in line.point][0]
                train.line_idx = line.idx
                # Set Train's position at the Town:
                if player_home_point.idx == line.point[0]:
                    train.position = 0
                else:
                    train.position = line.length
                # Add Train:
                player.add_train(train)
                self.map.add_train(train)
                self._trains[train.idx] = train
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
            while not self._stop_event.wait(game_config.TICK_TIME):
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
        """ Makes game tick. Updates dynamic game entities.
        """
        log(log.DEBUG, "Game Tick")

        # Update all markets and storages:
        for market in self.map.markets:
            if market.product < market.product_capacity:
                market.product = min(market.product + market.replenishment, market.product_capacity)
        for storage in self.map.storages:
            if storage.armor < storage.armor_capacity:
                storage.armor = min(storage.armor + storage.replenishment, storage.armor_capacity)

        # Update trains positions, process points:
        for train in self._trains.values():
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
                # If train.speed == 0:
                else:
                    if train.position == line.length:
                        self.train_in_point(train, line.point[1])
                    elif train.position == 0:
                        self.train_in_point(train, line.point[0])
            else:
                log(log.ERROR, "Wrong train.line_idx: {}".format(train.line_idx))

        # Update population and products in towns:
        for player in self._players.values():
            if player.town.product < player.town.population:
                player.town.population = max(player.town.population - 1, 0)
            player.town.product = max(player.town.product - player.town.population, 0)

        # Make assaults:
        self.hijackers_assault()
        self.parasites_assault()

    def train_in_point(self, train, point):
        """ Makes all needed actions when Train arrives to Point.
        Applies next Train move if exist, processes Post if exist in the Point.
        """
        log(log.INFO, "Train:{0} arrived to point:{1} position:{2} line:{3}".format(
            train.idx, point, train.position, train.line_idx))

        post_id = self.map.point[point].post_id
        if post_id is not None:
            self.train_in_post(train, self.map.post[post_id])

        if train.idx in self._next_train_moves:
            next_move = self._next_train_moves[train.idx]
            # If next line the same as previous:
            if next_move['line_idx'] == train.line_idx:
                if train.speed > 0 and train.position == self.map.line[train.line_idx].length:
                    train.speed = 0
                elif train.speed < 0 and train.position == 0:
                    train.speed = 0
            # If next line differs from previous:
            else:
                train.speed = next_move['speed']
                train.line_idx = next_move['line_idx']
                if train.speed > 0:
                    train.position = 0
                elif train.speed < 0:
                    train.position = self.map.line[train.line_idx].length
        # The train hasn't got next move data.
        else:
            train.speed = 0

    def move_train(self, train_idx, speed, line_idx):
        """ Process action MOVE. Changes path or speed of the Train.
        """
        with self._lock:
            if train_idx not in self._trains:
                return Result.RESOURCE_NOT_FOUND
            if train_idx in self._next_train_moves:
                del self._next_train_moves[train_idx]
            train = self._trains[train_idx]
            if line_idx not in self.map.line:
                return Result.RESOURCE_NOT_FOUND

            # Stop the train:
            if speed == 0:
                train.speed = speed

            # The train is standing:
            elif train.speed == 0:
                # Continue run the train:
                if train.line_idx == line_idx:
                    train.speed = speed
                # The train is standing at the end of the line:
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
                    else:
                        return Result.PATH_NOT_FOUND
                # The train is standing at the beginning of the line:
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
                    else:
                        return Result.PATH_NOT_FOUND
                # The train is standing on the line (between line's points), player have to continue run the train.
                else:
                    return Result.BAD_COMMAND

            # The train is moving on the line (between line's points):
            elif train.speed != 0 and train.line_idx != line_idx:
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

                # This train move request is valid and will be applied later:
                if switch_line_possible:
                    self._next_train_moves[train_idx] = {'speed': speed, 'line_idx': line_idx}
                # This train move request is invalid:
                else:
                    return Result.PATH_NOT_FOUND

        return Result.OKEY

    def train_in_post(self, train, post):
        """ Makes all needed actions when Train arrives to Post.
        Behavior depends on PostType, train can be loaded or unloaded.
        """
        if post.type == PostType.TOWN:
            # Unload product from train to town
            if train.post_type == PostType.MARKET:
                post.product += train.goods
            elif train.post_type == PostType.STORAGE:
                post.armor += train.goods

            train.goods = 0
            train.post_type = None

        elif post.type == PostType.MARKET:
            # Load product from market to train.
            if train.post_type is None or train.post_type == post.type:
                product = min(post.product, train.goods_capacity - train.goods)
                post.product -= product
                train.goods += product
                train.post_type = post.type

        elif post.type == PostType.STORAGE:
            # Load armor from storage to train.
            if train.post_type is None or train.post_type == post.type:
                armor = min(post.armor, train.goods_capacity - train.goods)
                post.armor -= armor
                train.goods += armor
                train.post_type = post.type

    def hijackers_assault(self):
        """ Makes hijackers assault which decreases quantity of Town's armor and population.
        """
        rand_percent = random.randint(1, 100)
        if rand_percent <= game_config.HIJACKERS_ASSAULT_PROBABILITY:
            hijackers_power = random.randint(*game_config.HIJACKERS_POWER_RANGE)
            log(log.INFO, "Hijackers assault happened, hijackers_power={}".format(hijackers_power))
            for player in self._players.values():
                player.town.population = max(player.town.population - max(hijackers_power - player.town.armor, 0), 0)
                player.town.armor = max(player.town.armor - hijackers_power, 0)

    def parasites_assault(self):
        """ Makes parasites assault which decreases quantity of Town's product.
        """
        rand_percent = random.randint(1, 100)
        if rand_percent <= game_config.PARASITES_ASSAULT_PROBABILITY:
            parasites_power = random.randint(*game_config.PARASITES_POWER_RANGE)
            log(log.INFO, "Parasites assault happened, parasites_power={}".format(parasites_power))
            for player in self._players.values():
                player.town.product = max(player.town.product - parasites_power, 0)
