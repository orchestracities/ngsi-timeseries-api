


class BaseTranslator(object):

    # Note: Some databases will restrict the possible names for tables and columns.
    TIME_INDEX_NAME = 'time_index'

    def __init__(self, host, port, db_name):
        self.host = host
        self.port = port
        self.db_name = db_name

    def setup(self):
        raise NotImplementedError

    def dispose(self):
        raise NotImplementedError

    def translate_to_ngsi(self, entries):
        raise NotImplementedError

    def translate_from_ngsi(self, entities):
        raise NotImplementedError

    def insert(self, entities):
        raise NotImplementedError

    def query(self, attr_name=None, entity_id=None):
        raise NotImplementedError

    def average(self, attr_name, entity_id=None):
        raise NotImplementedError
