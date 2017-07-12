from translators.base_translator import BaseTranslator
from utils.common import ATTR_TO_TYPE
import rethinkdb as rt


class RethinkTranslator(BaseTranslator):

    TABLE_NAME = "notifications"

    def __init__(self, host, port=28015, db_name="test"):
        super(RethinkTranslator, self).__init__(host, port, db_name)
        self.conn = None


    def setup(self):
        self.conn = rt.connect(self.host, self.port)
        # rt.db(self.db_name).table_drop(self.TABLE_NAME).run(self.conn)
        self.create_table()


    def dispose(self):
        rt.db(self.db_name).table_drop(self.TABLE_NAME).run(self.conn)
        self.conn.close()


    def create_table(self):
        res = rt.db(self.db_name).table_create(self.TABLE_NAME).run(self.conn)
        if res['tables_created'] != 1:
            raise RuntimeError("Could not create table '{}'".format(self.TABLE_NAME))


    def refresh(self):
        pass


    def translate_from_ngsi(self, entities):
        for entity in entities:
            entry = {}
            for k in entity:
                if k == 'type':
                    entry['entity_type'] = entity[k]
                elif k == 'id':
                    entry['entity_id'] = entity[k]
                elif k == BaseTranslator.TIME_INDEX_NAME:
                    entry[k] = entity[k]
                else:
                    entry[k] = entity[k]["value"]
            yield entry


    def translate_to_ngsi(self, entries):
        for e in entries:
            entity = {}
            for k, v in e.items():
                if k == 'id':
                    # RethinkDB gives an id to each object, which we ignore for now.
                    continue

                elif k == 'entity_type':
                    entity['type'] = v

                elif k == 'entity_id':
                    entity['id'] = v

                elif k == BaseTranslator.TIME_INDEX_NAME:
                    entity[k] = v

                else:
                    t = ATTR_TO_TYPE[k]
                    entity[k] = {'value': v, 'type': t}
            yield entity


    def insert(self, entities):
        entries = list(self.translate_from_ngsi(entities))
        op = rt.table(self.TABLE_NAME).insert(entries)
        res = op.run(self.conn)
        return res


    def query(self, attr_names=None, entity_type=None, entity_id=None):
        op = rt.table(self.TABLE_NAME)
        if attr_names:
            op = op.pluck(attr_names)
        if entity_id:
            op = op.filter(lambda x: rt.branch(x['entity_id'] == entity_id, True, False))
        res = op.run(self.conn)
        return self.translate_to_ngsi(res)


    def average(self, attr_name, entity_type=None, entity_id=None):
        if entity_id:
            op = rt.table(self.TABLE_NAME).filter({'entity_id': entity_id}).avg(attr_name)
        else:
            op = rt.table(self.TABLE_NAME).avg(attr_name)
        res = op.run(self.conn)
        return res
