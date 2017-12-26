# server.py

## Client-Server messages

### Common message format

Client sends to server some "action" messages and retrieves "response" message.
The **Action message** always begins from action code. On C++ language all possible action codes can be represents by enumeration:

```C++
enum Action
{
    LOGIN = 1,
    LOGOUT = 2,
    MOVE = 3,
    UPGRADE = 4,
    TURN = 5,
    MAP = 10
}
```

After action code (if necessary) follows data section.
As answer from server client gets **response message**. Response message starts with **result code**:

```C++
enum Result
{
    OKEY = 0
    BAD_COMMAND = 1
    RESOURCE_NOT_FOUND = 2
    PATH_NOT_FOUND = 3
    ACCESS_DENIED = 5
}
```

After result code follows (if it necessary) data section.
**Data section** format:
{data length (4 bytes)}+{bytes of UTF-8 string, contains data in JSON format}
So client-server messages can be represent by follow types:

```C++
struct ActionMessage
{
    Action actionCode;
    size_t dataLength;
    char data[];
}

struct ResposeMessage
{
    Result result;
    size_t dataLength;
    char data[];
}
```

### Login

This action message must be first in client-server "dialog". In data server expected to receive in data value **name**
For multi play game need define two additional values:

* **num_players** - number of players on the game
* **game** - game name

Non mandatory parameter **security_key** - uses for verification player connection for restore after disconnect.
If player with same name try reconnect to existing game with another **security_key** - login will be rejected.

#### Example login action bin data and message

Hex: |01 00 00 00|17 00 00 00|"{\n    "name": "Boris"\n}"

#### Response message example

``` JSON
{
    "home": {
        "idx": 1,
        "post_id": 1
    },
    "idx": "dd87709a-91bf-4e99-8b5e-49b3fd5776ac",
    "name": "Boris",
    "train": [
        {
            "idx": 0,
            "line_idx": 1,
            "player_id": "dd87709a-91bf-4e99-8b5e-49b3fd5776ac",
            "position": 0,
            "speed": 0
        }
    ]
}
```

#### Response key fields

* **home.idx** - home's point index
* **home.post_id** - home's post identifier
* **idx** - player's unique id (index)
* **train** - list of trains belongs to this player
  * **train[0].idx** - train id

### Logout

This action closes connection. Data empty.

### Map

Reads game map. Map loads by layers:

* Layer 0 - static objects
* Layer 1 - dynamic objects
* Layer 10 - coordinates of points

Layer 0 includes info about map index(idx), map name(name), lines(line), points(point)

#### Example map action bin data with message

Action MAP message:
Hex: |0A 00 00 00|0D 00 00 00|"{ "layer": 0 }"

#### Map JSON string data example for result of action MAP for layer=0

``` JSON
{
    "idx": 1,
    "line": [
      {
         "idx": 1,
         "length": 10,
         "point": [
             1,
             7
          ]
      },
      {
          "idx": 2,
          "length": 10,
          "point": [
              8,
              2
            ]
      },
        {
            "idx": 3,
            "length": 10,
            "point": [
                9,
                3
            ]
        },
        ...
    ],
    "name": "map01",
    "point": [
        {
            "idx": 1,
            "post_id": 1
        },
        {
            "idx": 2
        },
        {
            "idx": 3
        },
        ...
    ]
}
```

#### Map JSON string data example for result of action MAP for layer=1

``` JSON
{
    "idx": 1,
    "post": [
        {
            "armor": 0,
            "idx": 1,
            "name": "town-one",
            "population": 10,
            "product": 0,
            "type": 1
        }
    ],
    "rating": {
        "41acf370-e1f3-414d-8a35-50e00ff4930f": {
            "name": "Nikolay",
            "rating": 12345
        },
    },
    "train": [
        {
            "idx": 0,
            "line_idx": 1,
            "player_id": "dd87709a-91bf-4e99-8b5e-49b3fd5776ac",
            "position": 0,
            "speed": 0
        }
    ]
}
```

Layer 1 contains all dynamic objects on the map. In the example we got info about one post and one train.
Each __post__ has follows key fields:

* **idx** - unique post id
* **name** - post name
* **type** - post type

Each __train__ has follows key fields:

* **idx** - unique train id
* **line_idx** - line index where the train moves in the current moment
* **player_id** - id of player, who owner of this train
* **position** - position of this train in the current line
* **speed** - speed on the train

Rating of players calculated each turn and can be get from dictionary __rating__. The key on this dictionary - player name; value - rating score.

#### Map JSON string data example for result of action MAP for layer=10

``` JSON
'{
    "coordinate": [
        {
            "idx": 1,
            "x": 10,
            "y": 10
        },
        {
            "idx": 2,
            "x": 30,
            "y": 10
        },
        {
            "idx": 3,
            "x": 50,
            "y": 10
        },
        {
            "idx": 4,
            "x": 70,
            "y": 10
        },
        {
            "idx": 5,
            "x": 90,
            "y": 10
        }
    ],
    "size": [
        200,
        200
    ]
}'
```

Layer 10 contains coordinates for all points on the map. In the example we got coordinates of 5 points.
Also Layer 10 bring us size on the map.
Coordinates and size in logical units.
Each __coordinate__ includes:

* **idx** - point index
* **x** - x coordinate
* **y** - y coordinate

__size__ is array of two integers: **width** and **height**

### MOVE action

#### Example of message of MOVE action

``` JSON
{
    "line_idx": 1,
    "speed": 1,
    "train_idx": 0
}
```

**MOVE** action must send follow fields:

* **line_idx** - line index. Index of line where the train will be placed in start on the game or in the next point
* **speed** - speed of the point. Possible values:
  * 0 - the train will be stopped on the next point
  * 1 - the train moves in positive direction
  * -1 - the train moves in negative direction
* **train_idx** - index of the train

### UPGRADE action

#### Examples of message of UPGRADE action

``` JSON
{
    "post": [],
    "train": [1, 2]
}
```

``` JSON
{
    "post": [1],
    "train": []
}
```

**UPGRADE** action must send follow fields:

* **post** - list with unique indexes of posts to upgrade
* **train** - list with unique indexes of trains to upgrade

### TURN action

Turn action needs for force next turn of the game and don't wait game's time slice.
Game time slice equal to 1 second.
TURN action receives empty parameters.

#### Example turn action bin data

Hex: |05 00 00 00|02 00 00 00|"{}"

## The Game

### Two types of goods

In the game uses two types of resources (goods): product and armor

#### product

This type of resource (goods) uses for support the city's population. In a game turn 1 settler eats 1 product in the town.
Product can be mined by a train in a Market ( on the map this object defined as Post with type MARKET )
Products sometimes steal parasites! (See: Event:"Parasites Invasion")

#### armor

This type of resource (goods) uses for increase the town defence from bandits attack (see: Event:"Bandits Attack" item ) and upgrades units (see: Upgrade). On Bandits Attack decreases armor in the town (1 bandit ---> -1 armor).
Armor can be mined by a train in a Storage ( on the map this object defined as Post with type STORAGE )
If you have enough armor in the town - you can use it for upgrade the town it self or/and upgrade yours train(s)

### Events

In the game can happens something :). Player notified about it by events.
Each event binds to some game entity (Town, Train, etc.)
In current moment in the Game implements following type of events:

#### Events Types

```Python
    TRAIN_COLLISION = 1
    HIJACKERS_ASSAULT = 2
    PARASITES_ASSAULT = 3
    REFUGEES_ARRIVAL = 4
    RESOURCE_OVERFLOW = 5
    RESOURCE_LACK = 6
    GAME_OVER = 100
````

#### Parasites Invasion

This event binds to the Town.
Parasites eats products in the town. Products decrement count equal to parasites count in attack event.
Number of parasites in one attack [1..3]
Safe time after attack: 5 * (number parasites in last attack)

##### Map JSON string data example for result of action MAP for layer=1 with event "parasites attack"

``` JSON
{
    "idx": 1,
    "post": [
        {
        "type": 1,
        "name": "town-one",
        "event": [
            {
                "parasites_power": 3,
                "tick": 111,
                "type": 3
            }
        ],
        "product": 29,
        "product_capacity": 200,
        ...

        },
        ...
}
```

* **parasites_power** - count of parasites (count of products decreased in the town)
* **tick** - game's turn number
* **type** - event's type. This value equal to 3.

#### Bandits Attack

This event binds to the Town. "Bandits Attack" very same to "Parasites Invasion", but in this case decrements armor.
If the town has less armor than takes on this attack, than population of this town decreases by 1!
Number of bandits in one attack [1..3]
Safe time after attack: 5 * (number bandits in last attack)

##### Map JSON string data example for result of action MAP for layer=1 with event bandits attack

``` JSON
{
    "idx": 1,
    "post": [
        {
        "type": 1,
        "name": "town-one",
        "event": [
            {
                "hijackers_power": 2,
                "tick": 1,
                "type": 2
            }
        ],
        "product": 29,
        "product_capacity": 200,
            ...

        },
        ...
}
```

* **hijackers_power** - count of bandits (count of armors decreased in the town).
* **tick** - game's turn number
* **type** - event's type. This value equal to 2.

#### Arrival of Refugees

Increase population of the town.

##### Map JSON string data example for result of action MAP for layer=1 with event "refugees arrived"

``` JSON
{
    "idx": 1,
    "post": [
        {
        "type": 1,
        "name": "town-one",
        "event": [
            {
                "refugees_number": 2,
                "tick": 1,
                "type": 4
            }
        ],
        "product": 29,
        "product_capacity": 200,
        ...
        },
        ...
}
```

* **refugees_number** - count of population that increased in the town).
* **tick** - game's turn number
* **type** - event's type. This value equal to 4.

#### Train Crash

If two or more trains at same time and at the same point - this is the crash situation!
All trains participated in this crash immediately returns to it's town (on this turn) and all goods on the train will be nulled (set to 0).

##### Map JSON string data example for result of action MAP for layer=1 with event "trains crash"

``` JSON
{
    "idx": 1,
    ...
    "train": [
        {
            "event": [
                {
                    "tick": 2,
                    "train": 2,
                    "type": 1
                }
            ],
            "goods": 0,
            "goods_capacity": 40,
            "idx": 1,
            "level": 1,

            "line_idx": 1,
            "next_level_price": 40,
            "player_id": "5e0087f0-0f15-40a0-aa87-0ef2abce32cb",
            "position": 0,
            "post_type": null,
            "speed": 0
        },
        ...
}
```

* **tick** - game's turn number
* **train** - train ID with that was collision
* **type** - event's type. This value equal to 1.

### Upgrade

In some moment of the game the player have decide to upgrade his town or train.
All upgrades are paid by armor.
For initiate upgrade client sends to server action UPGRADE (protocol of action UPGRADE described above)

#### Town upgrade

What gets the town as a result of upgrade? See in following table:

Level | Population Capacity | Product Capacity | Armor Capacity | Crash Penalty | Next Level Price
------|---------------------|------------------|----------------|---------------|------------------
1 | 10 | 200 | 100 | 2 | 100
2 | 20 | 400 | 200 | 1 | 200
3 | 40 | 800 | 400 | 0 | None

Level 3 - is maximal town level

#### Train upgrade

What gets the train as a result of upgrade? See in following table:

Level | Goods Capacity | Next Level Price
------|----------------|------------------
1 | 40  | 40
2 | 80  | 80
3 | 160 | None

Level 3 - is maximal train level

### Rating

Rating value (game score) calculated on server every turn for each player.
This value figured on result of MAP(layer=1)

Calculation formula
rating = [population] *
         1000 + sum([upgrade level cost]) *
         10 + (town.product + town.armor)
where:

    * [population] = current population in player's town ( the value is multiplied by 1000 )
    * sum( [upgrade level cost] ) = sum armor spent for upgrades all units (train(s), town) ( the value is multiplied by 10 )
    * (town.product + town.armor) = sum accumulated values of armor and product in player's town
