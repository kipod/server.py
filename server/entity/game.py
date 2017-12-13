""" Game entity.
"""
import math
import json
import random
from threading import Thread, Event, Lock

from db.replay import DbReplay
from defs import Result, Action
from entity.event import EventType, Event as GameEvent
from entity.map import Map
from entity.player import Player
from entity.point import Point
from entity.post import PostType, Post
from entity.train import Train
from game_config import config
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

    def __init__(self, name, map_name=config.MAP_NAME, observed=False, num_players=1):
        super(Game, self).__init__(name=name)
        log(log.INFO, "Create game, name: '{}'".format(self.name))
        self.observed = observed
        self.replay = None if self.observed else DbReplay()
        self.map = Map(map_name)
        self.current_game_id = 0 if self.observed else self.replay.add_game(name, map_name=self.map.name)
        self.current_tick = 0
        self.players = {}
        self.name = name
        self.trains = {}
        self.skip_next_tick = False
        self.next_train_moves = {}
        self.event_cooldowns = {}
        self._lock = Lock()
        self._stop_event = Event()
        self._num_players = num_players
        random.seed()

    @staticmethod
    def create(name, num_players=1):
        """ Returns instance of class Game.
        """
        if name in Game.GAMES:
            game = Game.GAMES[name]
        else:
            Game.GAMES[name] = game = Game(name, num_players=num_players)
        return game

    @num_players.getter
    def num_players(self):
        """ getter property num_players """
        return self._num_players

    def add_player(self, player: Player):
        """ Adds player to the game.
        """
        if player.idx not in self.players:
            with self._lock:
                # Use first Town on the map as player's Town:
                player_town = self.map.towns[0]
                player_home_point = self.map.point[player_town.point_id]
                player.set_home(player_home_point, player_town)
                self.players[player.idx] = player
                # Add trains for the player:
                for _ in range(config.DEFAULT_TRAINS_COUNT):
                    # Create Train:
                    train = Train(idx=len(self.trains) + 1)
                    # Add Train:
                    player.add_train(train)
                    self.map.add_train(train)
                    self.trains[train.idx] = train
                    # Put the Train into Town:
                    self.put_train_into_town(train, with_cooldown=False)
                log(log.INFO, "Add new player to the game, player: {}".format(player))
            if not self.observed:
                Thread.start(self)

    def turn(self):
        """ Makes next turn.
        """
        self.skip_next_tick = True
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
            while not self._stop_event.wait(config.TICK_TIME):
                with self._lock:
                    if self.skip_next_tick:
                        self.skip_next_tick = False
                    else:
                        self.tick()
                        if replay:
                            replay.add_action(
                                Action.TURN, message=None, with_commit=False, game_id=self.current_game_id
                            )
            if replay:
                replay.commit()
        finally:
            if replay:
                replay.close()

    def tick(self):
        """ Makes game tick. Updates dynamic game entities.
        """
        self.current_tick += 1
        log(log.INFO, "Game tick, tick number: {}".format(self.current_tick))
        self.update_cooldowns_on_tick()  # Update cooldowns in the beginning of the tick.
        self.update_posts_on_tick()
        self.update_trains_positions_on_tick()
        self.handle_trains_collisions_on_tick()
        self.process_trains_points_on_tick()
        self.update_towns_on_tick()
        self.refugees_arrival_on_tick()
        self.hijackers_assault_on_tick()
        self.parasites_assault_on_tick()

    def train_in_point(self, train: Train, point_id: int):
        """ Makes all needed actions when Train arrives to Point.
        Applies next Train move if it exist, processes Post if exist in the Point.
        """
        msg = "Train is in point, train: {}, point: {}".format(train, self.map.point[point_id])

        post_id = self.map.point[point_id].post_id
        if post_id is not None:
            msg += ", post: {!r}".format(self.map.post[post_id].type)
            self.train_in_post(train, self.map.post[post_id])

        log(log.INFO, msg)

        self.apply_next_train_move(train)

    def apply_next_train_move(self, train: Train):
        """ Applies postponed Train MOVE if it exist.
        """
        if train.idx in self.next_train_moves:
            next_move = self.next_train_moves[train.idx]
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
            if train_idx in self.next_train_moves:
                del self.next_train_moves[train_idx]
            train = self.trains[train_idx]
            if line_idx not in self.map.line:
                return Result.RESOURCE_NOT_FOUND

            # Check cooldown for the train:
            if train.cooldown > 0:
                return Result.BAD_COMMAND

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
                    self.next_train_moves[train_idx] = {'speed': speed, 'line_idx': line_idx}
                # This train move request is invalid:
                else:
                    return Result.PATH_NOT_FOUND

        return Result.OKEY

    def train_in_post(self, train: Train, post: Post):
        """ Makes all needed actions when Train arrives to Post.
        Behavior depends on PostType, train can be loaded or unloaded.
        """
        if post.type == PostType.TOWN:
            # Unload product from train to town:
            goods = 0
            if train.post_type == PostType.MARKET:
                goods = max(min(train.goods, post.product_capacity - post.product), 0)
                post.product += goods
                if post.product == post.product_capacity:
                    post.event.append(GameEvent(EventType.RESOURCE_OVERFLOW, self.current_tick, product=post.product))
            elif train.post_type == PostType.STORAGE:
                goods = max(min(train.goods, post.armor_capacity - post.armor), 0)
                post.armor += goods
                if post.armor == post.armor_capacity:
                    post.event.append(GameEvent(EventType.RESOURCE_OVERFLOW, self.current_tick, armor=post.armor))
            train.goods -= goods
            if train.goods == 0:
                train.post_type = None

        elif post.type == PostType.MARKET:
            # Load product from market to train:
            if train.post_type is None or train.post_type == post.type:
                product = max(min(post.product, train.goods_capacity - train.goods), 0)
                post.product -= product
                train.goods += product
                train.post_type = post.type

        elif post.type == PostType.STORAGE:
            # Load armor from storage to train:
            if train.post_type is None or train.post_type == post.type:
                armor = max(min(post.armor, train.goods_capacity - train.goods), 0)
                post.armor -= armor
                train.goods += armor
                train.post_type = post.type

    def put_train_into_town(self, train: Train, with_unload=True, with_cooldown=True):
        """ Puts given Train to his Town.
        """
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
        # Set cooldown for the Train:
        if with_cooldown:
            # Get Train owner's town:
            player_town = self.players[train.player_id].town
            train.cooldown = player_town.train_cooldown_on_collision

    def hijackers_assault_on_tick(self):
        """ Makes hijackers assault which decreases quantity of Town's armor and population.
        """
        # Check cooldown for this Event:
        if self.event_cooldowns.get(EventType.HIJACKERS_ASSAULT, 0) > 0:
            return

        rand_percent = random.randint(1, 100)
        if rand_percent <= config.HIJACKERS_ASSAULT_PROBABILITY:
            hijackers_power = random.randint(*config.HIJACKERS_POWER_RANGE)
            log(log.INFO, "Hijackers assault happened, hijackers power: {}".format(hijackers_power))
            event = GameEvent(EventType.HIJACKERS_ASSAULT, self.current_tick, hijackers_power=hijackers_power)
            for player in self.players.values():
                player.town.population = max(player.town.population - max(hijackers_power - player.town.armor, 0), 0)
                player.town.armor = max(player.town.armor - hijackers_power, 0)
                player.town.event.append(event)
            if self.replay:
                self.replay.add_action(Action.EVENT, event.to_json_str(), with_commit=False)
            self.event_cooldowns[EventType.HIJACKERS_ASSAULT] = round(
                hijackers_power * config.HIJACKERS_COOLDOWN_COEF)

    def parasites_assault_on_tick(self):
        """ Makes parasites assault which decreases quantity of Town's product.
        """
        # Check cooldown for this Event:
        if self.event_cooldowns.get(EventType.PARASITES_ASSAULT, 0) > 0:
            return

        rand_percent = random.randint(1, 100)
        if rand_percent <= config.PARASITES_ASSAULT_PROBABILITY:
            parasites_power = random.randint(*config.PARASITES_POWER_RANGE)
            log(log.INFO, "Parasites assault happened, parasites power: {}".format(parasites_power))
            event = GameEvent(EventType.PARASITES_ASSAULT, self.current_tick, parasites_power=parasites_power)
            for player in self.players.values():
                player.town.product = max(player.town.product - parasites_power, 0)
                player.town.event.append(event)
            if self.replay:
                self.replay.add_action(Action.EVENT, event.to_json_str(), with_commit=False)
            self.event_cooldowns[EventType.PARASITES_ASSAULT] = round(
                parasites_power * config.PARASITES_COOLDOWN_COEF)

    def refugees_arrival_on_tick(self):
        """ Makes refugees arrival which increases quantity of Town's population.
        """
        # Check cooldown for this Event:
        if self.event_cooldowns.get(EventType.REFUGEES_ARRIVAL, 0) > 0:
            return

        rand_percent = random.randint(1, 100)
        if rand_percent <= config.REFUGEES_ARRIVAL_PROBABILITY:
            refugees_number = random.randint(*config.REFUGEES_NUMBER_RANGE)
            log(log.INFO, "Refugees arrival happened, refugees number: {}".format(refugees_number))
            event = GameEvent(EventType.REFUGEES_ARRIVAL, self.current_tick, refugees_number=refugees_number)
            for player in self.players.values():
                player.town.population += max(
                    min(player.town.population_capacity - player.town.population, refugees_number), 0
                )
                player.town.event.append(event)
                if player.town.population == player.town.population_capacity:
                    player.town.event.append(
                        GameEvent(EventType.RESOURCE_OVERFLOW, self.current_tick, population=player.town.population)
                    )
            if self.replay:
                self.replay.add_action(Action.EVENT, event.to_json_str(), with_commit=False)
            self.event_cooldowns[EventType.REFUGEES_ARRIVAL] = round(
                refugees_number * config.REFUGEES_COOLDOWN_COEF)

    def update_posts_on_tick(self):
        """ Updates all markets and storages.
        """
        for market in self.map.markets:
            if market.product < market.product_capacity:
                market.product = max(min(market.product + market.replenishment, market.product_capacity), 0)
        for storage in self.map.storages:
            if storage.armor < storage.armor_capacity:
                storage.armor = max(min(storage.armor + storage.replenishment, storage.armor_capacity), 0)

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
            if player.town.population == 0:
                player.town.event.append(GameEvent(EventType.GAME_OVER, self.current_tick, population=0))
            if player.town.product == 0:
                player.town.event.append(GameEvent(EventType.RESOURCE_LACK, self.current_tick, product=0))
            if player.town.armor == 0:
                player.town.event.append(GameEvent(EventType.RESOURCE_LACK, self.current_tick, armor=0))

    @staticmethod
    def get_sign(variable):
        """ Returns sign of the variable.
         1 if variable >  0
        -1 if variable <  0
         0 if variable == 0
        """
        return variable and (1, -1)[variable < 0]

    def is_train_at_point(self, train: Train, point_to_check: Point = None):
        """ Returns Point if the Train at some Point now, else returns False.
        """
        line = self.map.line[train.line_idx]
        if train.position == line.length or train.position == 0:
            point_id = line.point[self.get_sign(train.position)]
            point = self.map.point[point_id]
            if point_to_check is None or point_to_check.idx == point.idx:
                return point
        return False

    def is_train_at_post(self, train: Train, post_to_check: Post = None):
        """ Returns Post if the Train at some Post now, else returns False.
        """
        point = self.is_train_at_point(train)
        if point and point.post_id:
            post = self.map.post[point.post_id]
            if post_to_check is None or post_to_check.idx == post.idx:
                return post
        return False

    def make_collision(self, train_1: Train, train_2: Train):
        """ Makes collision between two trains.
        """
        log(log.INFO, "Trains collision happened, trains: [{}, {}]".format(train_1, train_2))
        self.put_train_into_town(train_1, with_unload=True, with_cooldown=True)
        self.put_train_into_town(train_2, with_unload=True, with_cooldown=True)
        train_1.event.append(GameEvent(EventType.TRAIN_COLLISION, self.current_tick, train=train_2.idx))
        train_2.event.append(GameEvent(EventType.TRAIN_COLLISION, self.current_tick, train=train_1.idx))

    def handle_trains_collisions_on_tick(self):
        """ Handles Trains collisions.
        """
        collision_pairs = []
        trains = list(self.trains.values())
        for i, train_1 in enumerate(trains):
            # Get Line and Point of train_1:
            line_1 = self.map.line[train_1.line_idx]
            point_1 = self.is_train_at_point(train_1)
            for train_2 in trains[i + 1:]:
                # Get Line and Point of train_2:
                line_2 = self.map.line[train_2.line_idx]
                point_2 = self.is_train_at_point(train_2)
                # If train_1 and train_2 at the same Point:
                if point_1 and point_2 and point_1.idx == point_2.idx:
                    post = None if point_1.post_id is None else self.map.post[point_1.post_id]
                    if post is not None and post.type in (PostType.TOWN, ):
                        continue
                    else:
                        collision_pairs.append((train_1, train_2))
                        continue
                # If train_1 and train_2 on the same Line:
                if line_1.idx == line_2.idx:
                    # If train_1 and train_2 have the same position:
                    if train_1.position == train_2.position:
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
        for pair in collision_pairs:
            self.make_collision(*pair)

    def make_upgrade(self, player: Player, post_ids=(), train_ids=()):
        """ Upgrades given Posts and Trains to next level.
        """
        with self._lock:
            # Get posts from request:
            posts = []
            for post_id in post_ids:
                if post_id not in self.map.post:
                    return Result.RESOURCE_NOT_FOUND
                post = self.map.post[post_id]
                if post.type != PostType.TOWN:
                    return Result.BAD_COMMAND
                posts.append(post)

            # Get trains from request:
            trains = []
            for train_id in train_ids:
                if train_id not in self.trains:
                    return Result.RESOURCE_NOT_FOUND
                train = self.trains[train_id]
                trains.append(train)

            # Check existence of next level for each entity:
            posts_has_next_lvl = all([p.level + 1 in config.TOWN_LEVELS for p in posts])
            trains_has_next_lvl = all([t.level + 1 in config.TRAIN_LEVELS for t in trains])
            if not all([posts_has_next_lvl, trains_has_next_lvl]):
                return Result.BAD_COMMAND

            # Check armor quantity for upgrade:
            armor_to_up_posts = sum([p.next_level_price for p in posts])
            armor_to_up_trains = sum([t.next_level_price for t in trains])
            if player.town.armor < sum([armor_to_up_posts, armor_to_up_trains]):
                return Result.BAD_COMMAND

            # Check that trains are in town now:
            for train in trains:
                if not self.is_train_at_post(train, post_to_check=player.town):
                    return Result.BAD_COMMAND

            # Upgrade entities:
            for post in posts:
                player.town.armor -= post.next_level_price
                post.set_level(post.level + 1)
                log(log.INFO, "Post has been upgraded, post: {}".format(post))
            for train in trains:
                player.town.armor -= train.next_level_price
                train.set_level(train.level + 1)
                log(log.INFO, "Train has been upgraded, post: {}".format(train))

        return Result.OKEY

    def get_map_layer(self, layer):
        """ Returns specified game map layer.
        """
        if layer in (0, 1, 10):
            log(log.INFO, "Load game map layer, layer: {}".format(layer))
            message = self.map.layer_to_json_str(layer)
            self.clean_events()
            if layer == 1:  # Add ratings.
                data = json.loads(message)
                rating = {}
                for player in self.players.values():
                    rating[player.name] = player.rating
                data['rating'] = rating
                message = json.dumps(data, sort_keys=True, indent=4)
            return Result.OKEY, message
        else:
            return Result.RESOURCE_NOT_FOUND, None

    def clean_events(self):
        """ Cleans all existing events.
        """
        for train in self.map.train.values():
            train.event = []
        for post in self.map.post.values():
            post.event = []

    def update_cooldowns_on_tick(self):
        """ Decreases all cooldown values on game tick.
        """
        # Update cooldowns for random events:
        for event in self.event_cooldowns:
            if self.event_cooldowns[event] != 0:
                self.event_cooldowns[event] = max(self.event_cooldowns[event] - 1, 0)

        # Update cooldowns for trains:
        for train in self.trains.values():
            if train.cooldown != 0:
                train.cooldown = max(train.cooldown - 1, 0)
