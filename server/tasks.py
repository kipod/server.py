""" WG Forge server tasks.
"""
from db.shell import dbshell  # noqa F401
from db.map import generate_map  # noqa F401
from db.replay import generate_replay  # noqa F401
from server import run_server  # noqa F401
