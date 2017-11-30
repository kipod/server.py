from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from defs import MAP_DB_URI, REPLAY_DB_URI

map_engine = create_engine(MAP_DB_URI)
replay_engine = create_engine(REPLAY_DB_URI)

MapSession = sessionmaker(bind=map_engine)
ReplaySession = sessionmaker(bind=replay_engine)
