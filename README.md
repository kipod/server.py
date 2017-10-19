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

This action message must be first in client-server "dialog".