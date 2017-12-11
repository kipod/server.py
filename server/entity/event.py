from enum import IntEnum

from entity.serializable import Serializable


class EventType(IntEnum):
    """ Types of an Event.
    """
    TRAIN_COLLISION = 1
    HIJACKERS_ASSAULT = 2
    PARASITES_ASSAULT = 3
    REFUGEES_ARRIVAL = 4
    RESOURCE_OVERFLOW = 5
    RESOURCE_LACK = 6
    GAME_OVER = 100


class Event(Serializable):
    """ Event entity defined by: EventType, game tick and additional info.
    """
    def __init__(self, event_type: EventType, tick, **kwargs):
        self.type = event_type
        self.tick = tick
        for key, value in kwargs.items():  # Additional info from kwargs.
            setattr(self, key, value)

    def __repr__(self):
        return "<Event(type={}, tick={})>".format(self.type, self.tick)
