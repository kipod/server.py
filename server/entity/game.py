""" Game entity.
"""
import math
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
        log(log.INFO, "Create game, name: '{}'".format(self.name))
        self.replay = None
        self._observed = observed
        if not observed:
            self.replay = DbReplay()
        self._lock = Lock()
        self._current_game_id = 0
        self._current_tick = 0
        self.players = {}
        self.map = Map(map_name)
        self.name = name
        self.trains = {}
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
        if player.idx not in self.players:
            # Use first Town on the map as player's Town:
            player_town = self.map.towns[0]
            player_home_point = self.map.point[player_town.point_id]
            player.set_home(player_home_point, player_town)
            self.players[player.idx] = player
            # Add trains for the player:
            for _ in range(game_config.DEFAULT_TRAINS_COUNT):
                # Create Train:
                train = Train(idx=len(self.trains) + 1)
                # Add Train:
                player.add_train(train)
                self.map.add_train(train)
                self.trains[train.idx] = train
                # Put the Train into Town:
                self.put_train_into_town(train)
            log(log.INFO, "Add new player to the game, player: {}".format(player))
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
        log(log.INFO, "Game stopped, name: '{}'".format(self.name))
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
        self._current_tick += 1
        log(log.DEBUG, "Game tick, tick number: {}".format(self._current_tick))
        self.update_posts_on_tick()
        self.update_trains_positions_on_tick()
        self.handle_trains_collisions_on_tick()
        self.process_trains_points_on_tick()
        self.update_towns_on_tick()
        self.hijackers_assault_on_tick()
        self.parasites_assault_on_tick()

    def train_in_point(self, train, point_id):
        """ Makes all needed actions when Train arrives to Point.
        Applies next Train move if exist, processes Post if exist in the Point.
        """
        msg = "Train is in point, train: {}, point: {}".format(train, self.map.point[point_id])

        post_id = self.map.point[point_id].post_id
        if post_id is not None:
            msg += ", post: {!r}".format(self.map.post[post_id].type)
            self.train_in_post(train, self.map.post[post_id])

        log(log.INFO, msg)

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
            if train_idx not in self.trains:
                return Result.RESOURCE_NOT_FOUND
            if train_idx in self._next_train_moves:
                del self._next_train_moves[train_idx]
            train = self.trains[train_idx]
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

    def put_train_into_town(self, train, with_unload=True):
        # Get Train owner's home point:
        player_home_point = self.players[train.player_id].home
        # Use first Line connected to the home point as default train's line:
        line = [l for l in self.map.line.values() if player_home_point.idx in l.point][0]
        train.line_idx = line.idx
        # Set Train's position at the Town:
        if player_home_point.idx == line.point[0]:
            train.position = 0
        else:
            train.position = line.length
        # Stop Train:
        train.speed = 0
        # Unload the Train:
        if with_unload:
            train.goods = 0
            train.post_type = None

    def hijackers_assault_on_tick(self):
        """ Makes hijackers assault which decreases quantity of Town's armor and population.
        """
        rand_percent = random.randint(1, 100)
        if rand_percent <= game_config.HIJACKERS_ASSAULT_PROBABILITY:
            hijackers_power = random.randint(*game_config.HIJACKERS_POWER_RANGE)
            log(log.INFO, "Hijackers assault happened, hijackers power: {}".format(hijackers_power))
            for player in self.players.values():
                player.town.population = max(player.town.population - max(hijackers_power - player.town.armor, 0), 0)
                player.town.armor = max(player.town.armor - hijackers_power, 0)

    def parasites_assault_on_tick(self):
        """ Makes parasites assault which decreases quantity of Town's product.
        """
        rand_percent = random.randint(1, 100)
        if rand_percent <= game_config.PARASITES_ASSAULT_PROBABILITY:
            parasites_power = random.randint(*game_config.PARASITES_POWER_RANGE)
            log(log.INFO, "Parasites assault happened, parasites power: {}".format(parasites_power))
            for player in self.players.values():
                player.town.product = max(player.town.product - parasites_power, 0)

    def update_posts_on_tick(self):
        """ Updates all markets and storages.
        """
        for market in self.map.markets:
            if market.product < market.product_capacity:
                market.product = min(market.product + market.replenishment, market.product_capacity)
        for storage in self.map.storages:
            if storage.armor < storage.armor_capacity:
                storage.armor = min(storage.armor + storage.replenishment, storage.armor_capacity)

    def update_trains_positions_on_tick(self):
        """ Update trains positions.
        """
        for train in self.trains.values():
            line = self.map.line[train.line_idx]
            if train.speed > 0 and train.position < line.length:
                train.position += 1
            elif train.speed < 0 and train.position > 0:
                train.position -= 1

    def process_trains_points_on_tick(self):
        """ Update trains positions, process points.
        """
        for train in self.trains.values():
            line = self.map.line[train.line_idx]
            if train.position == line.length or train.position == 0:
                self.train_in_point(train, line.point[self.get_sign(train.position)])

    def update_towns_on_tick(self):
        """ Update population and products in Towns.
        """
        for player in self.players.values():
            if player.town.product < player.town.population:
                player.town.population = max(player.town.population - 1, 0)
            player.town.product = max(player.town.product - player.town.population, 0)

    @staticmethod
    def get_sign(variable):
        """ Returns sign of the variable.
         1 if variable >  0
        -1 if variable <  0
         0 if variable == 0
        """
        return variable and (1, -1)[variable < 0]

    def is_train_at_post(self, train):
        """ Returns Post if the Train at some Post now, else returns None.
        """
        line = self.map.line[train.line_idx]
        if train.position == line.length or train.position == 0:
            point_id = line.point[self.get_sign(train.position)]
            point = self.map.point[point_id]
            if point.post_id:
                return self.map.post[point.post_id]
        return None

    def make_collision(self, train_1, train_2):
        """ Makes collision between two trains.
        """
        log(log.INFO, "Trains collision happened, trains: [{}, {}]".format(train_1, train_2))
        self.put_train_into_town(train_1, with_unload=True)
        self.put_train_into_town(train_2, with_unload=True)
        # TODO: Create event here.

    def handle_trains_collisions_on_tick(self):
        """ Handles Trains collisions.
        """
        collision_pairs = []
        trains = list(self.trains.values())
        for i, train_1 in enumerate(trains):
            # Get Line and Post of train_1:
            line_1 = self.map.line[train_1.line_idx]
            post_1 = self.is_train_at_post(train_1)
            for train_2 in trains[i + 1:]:
                # Get Line and Post of train_2:
                line_2 = self.map.line[train_2.line_idx]
                post_2 = self.is_train_at_post(train_2)
                # If train_1 and train_2 on the same Line:
                if line_1.idx == line_2.idx:
                    # If train_1 and train_2 have the same position and they are not at Post:
                    if train_1.position == train_2.position and not (post_1 or post_2):
                        collision_pairs.append((train_1, train_2))
                        continue
                    # Skip if train_1 or train_2 has been stopped and they have different positions:
                    if train_1.speed == 0 or train_2.speed == 0:
                        continue
                    # Calculating distance between train_1 and train_2 now and after next tick:
                    train_step_1 = self.get_sign(train_1.speed)
                    train_step_2 = self.get_sign(train_2.speed)
                    dist_before_tick = math.fabs(train_1.position - train_2.position)
                    dist_after_tick = math.fabs(train_1.position + train_step_1 - train_2.position + train_step_2)
                    # If after next tick train_1 and train_2 cross:
                    if dist_before_tick == dist_after_tick == 1 and train_step_1 + train_step_2 == 0:
                        collision_pairs.append((train_1, train_2))
                        continue
                # If train_1 and train_2 at the same Post:
                if post_1 and post_2 and post_1.idx == post_2.idx:
                    if post_1.type not in (PostType.TOWN, ):
                        collision_pairs.append((train_1, train_2))
                        continue
        for pair in collision_pairs:
            self.make_collision(*pair)
