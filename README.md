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
    RUN = 3,
    STOP = 4,
    NEXT = 5,
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

#### Example

Hex: |01 00 00 00|17 00 00 00|"{\n    "name": "Boris"\n}"

### Logout

This action closes connection. Data empty.

### Map

Reads game map. Map loads by layers:

* Layer 0 - static objects
* Layer 1 - dynamic objects

Layer 0 includes info about map index(idx), map name(name), lines(line), points(point)

#### Example

Action MAP message:
Hex: |0A 00 00 00|0D 00 00 00|"{ "layer": 0 }"

Map JSON string data example for result of action MAP for layer=0:

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
        /*...*/
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
        /*...*/
    ]
}
```
