import sys
import types
from unittest.mock import MagicMock

import mysql.connector

# The bot reads its settings from config.py and opens a database connection while importing util.airing,
# so both are replaced before any test imports a cog.
config = types.ModuleType('config')
config.database = {'host': 'localhost', 'user': 'test', 'password': 'test', 'name': 'test'}
config.role = {'user': 1, 'global_mod': 2, 'anime_mod': 3}
config.channel = {'cots': 10, 'anime_forum': 11}
config.cache_dir = '/tmp/haamcbot-test-cache'
sys.modules['config'] = config

mysql.connector.connect = MagicMock()
