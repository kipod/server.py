#pragma once

class enum Action: public uint32_t
{
    LOGIN = 1,
    LOGOUT = 2,
    MOVE = 3,
    TURN = 5,
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