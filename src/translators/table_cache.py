import json


class Borg:
    __monostate = None

    def __init__(self):
        if not Borg.__monostate:
            Borg.__monostate = self.__dict__
            # Your definitions here
            self.cache = {}

        else:
            self.__dict__ = Borg.__monostate


class TableCacheManager(Borg):

    def add(self, table, attrs=None):
        if attrs:
            self.cache[table] = attrs
        else:
            self.cache[table] = {}

    def check(self, table, attrs=None):
        if table and table in self.cache.keys():
            if not attrs:
                return True
            elif self.cache[table] == attrs:
                return True
        else:
            return False

    def get(self, table):
        if table and table in self.cache.keys():
            return self.cache[table]
        else:
            return None

    def str(self):
        return json.dumps(self.cache)

    def pop(self, table):
        self.cache.pop(table)

    def clear(self):
        self.cache.clear()
