

class BaseTranslator(object):
    """
    Base class, trying to capture an interface, to be used for all the translators (NGSI to specific TSDBs).

    The usage after instantiation assumes setup is called first and dispose at last.
    """

    # Note: Some databases will restrict the possible names for tables and columns.
    TIME_INDEX_NAME = 'time_index'

    def __init__(self, host, port, db_name):
        self.host = host
        self.port = port
        self.db_name = db_name

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dispose()

    def setup(self):
        raise NotImplementedError

    def dispose(self):
        raise NotImplementedError

    def translate_to_ngsi(self, entries):
        raise NotImplementedError

    def translate_from_ngsi(self, entities):
        raise NotImplementedError

    def insert(self, entities):
        """
        :param entities:
            List of NGSI entities in JSON representation format.
            One of the attributes is expected to be TIME_INDEX_NAME, which will be used as the time index for the
            notifications.
        """
        raise NotImplementedError

    def query(self, attr_name=None, entity_id=None):
        raise NotImplementedError

    def average(self, attr_name, entity_id=None):
        raise NotImplementedError
