""" Sqlalchemy session fabrics and engines for each DB.
"""
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from defs import MAP_DB_URI, REPLAY_DB_URI

map_engine = create_engine(MAP_DB_URI)
replay_engine = create_engine(REPLAY_DB_URI)

MapSession = sessionmaker(bind=map_engine)
ReplaySession = sessionmaker(bind=replay_engine)


def _session_ctx(session_fabric):
    session = session_fabric()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def map_session_ctx():
    return _session_ctx(MapSession)


@contextmanager
def replay_session_ctx():
    return _session_ctx(ReplaySession)
