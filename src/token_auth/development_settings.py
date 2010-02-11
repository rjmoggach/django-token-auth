from settings import *

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'hashish.db'

try:
    from local_settings import *
except ImportError:
    pass


