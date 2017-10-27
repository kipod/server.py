# server.py

## Client-Server messages

### Common message format

Client sends to server some "action" messages and retrieves "response" message.
The **Action message** always begins from action code. On C++ language all possible action codes can be represents by enumeration:

```C++
class enum Action: public uint32_t
{
    LOGIN = 1,
    LOGOUT = 2,
    MOVE = 3,
    TURN = 5,
    MAP = 10
}
```

After action code (if necessary) follows data section.
As answer from server client gets **response message**. Response message starts with **result code**:

```C++
class enum Result: public uint32_t
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
