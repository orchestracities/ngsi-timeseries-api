class Borg:
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class ConnectionManager(Borg):

    connection = {}

    def __init__(self):
        Borg.__init__(self)

    def set_connection(self, db, connection):
        self.connection[db] = connection

    def get_connection(self, db):
        try:
            return self.connection[db]
        except KeyError as e:
            return None

    def reset_connection(self, db):
        self.connection[db] = None
