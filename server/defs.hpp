#pragma once

class enum Action: public uint32_t
{
    LOGIN = 1,
    LOGOUT = 2,
    RUN = 3,
    STOP = 4,
    NEXT = 5,
    TURN = 6,
    MAP = 10
}

class enum Result: public uint32_t
{
    OKEY = 0
    BAD_COMMAND = 1
    RESOURCE_NOT_FOUND = 2
    PATH_NOT_FOUND = 3
    ACCESS_DENIED = 5
}

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