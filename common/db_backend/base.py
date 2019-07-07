from django.db.backends.mysql.base import *

class DatabaseWrapper(DatabaseWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.force_debug_cursor = True
