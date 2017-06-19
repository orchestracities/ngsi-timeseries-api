from crate import client
from datetime import datetime, timedelta
from translators.base_translator import BaseTranslator
from utils.common import ATTR_TO_TYPE
from utils.hosts import LOCAL


class CrateTranslator(BaseTranslator):

    TABLE_NAME = "notifications"

    def __init__(self, host=LOCAL, port=4200, db_name="ngsi-tsdb"):
        super(CrateTranslator, self).__init__(host, port, db_name)


    def setup(self):
        self.conn = client.connect(["{}:{}".format(self.host, self.port)], error_trace=True)
        self.cursor = self.conn.cursor()
        self.create_table()


    def dispose(self):
        self.cursor.close()
        self.conn.close()


    def create_table(self):
        self.cursor.execute("DROP TABLE IF EXISTS {}".format(self.TABLE_NAME))
        self.cursor.execute("create table {} ( \
                        {} timestamp, \
                        attr_time timestamp, \
                        entity_type string, \
                        entity_id string, \
                        attr_bool boolean, \
                        attr_float float, \
                        attr_str string, \
                        attr_geo geo_shape)".format(self.TABLE_NAME, self.TIME_INDEX_NAME))


    def refresh(self):
        self.cursor.execute("refresh table {}".format(self.TABLE_NAME))


    def translate_from_ngsi(self, entities):
        for entity in entities:
            row = []
            for k in sorted(entity):
                if k in ('type', 'id', self.TIME_INDEX_NAME):
                    row.append(entity[k])
                else:
                    row.append(entity[k]["value"])
            yield row


    def _get_isoformat(self, ms_since_epoch):
        if ms_since_epoch is None:
            raise
        utc = datetime(1970, 1, 1, 0, 0, 0, 0) + timedelta(milliseconds=ms_since_epoch)
        # chopping last 3 digits of microseconds to avoid annoying diffs in testing
        return utc.isoformat()[:-3]


    def translate_to_ngsi(self, resultset, keys):
        for r in resultset:
            entity = {}
            for k, v in zip(keys, r):
                if k == 'entity_type':
                    entity['type'] = v
                elif k == 'entity_id':
                    entity['id'] = v
                elif k == self.TIME_INDEX_NAME:
                    # From CrateDB docs: Timestamps are always returned as long values (ms from epoch)
                    entity[self.TIME_INDEX_NAME] = self._get_isoformat(v)
                else:
                    t = ATTR_TO_TYPE[k]
                    entity[k] = {'value': v, 'type': t}
                    # same as above
                    if t == 'DateTime' and entity[k]['value']:
                        entity[k]['value'] = self._get_isoformat(entity[k]['value'])

            yield entity


    def insert(self, entities):
        # NOTE: Assuming all entities come with same columns! TODO: fix this
        col_names = ",".join(sorted(entities[0].keys()))
        col_names = col_names.replace('type', 'entity_type')
        col_names = col_names.replace('id', 'entity_id')
        entries = list(self.translate_from_ngsi(entities))
        op = "insert into {} ({}) values ({})".format(self.TABLE_NAME, col_names, ','.join('?'*len(entities[0])))
        self.cursor.executemany(op, entries)
        return self.cursor


    def query(self, attr_names=None, entity_id=None, where_clause=None):
        select_clause = "{}".format(attr_names[0]) if attr_names else "*"  # TODO: support some attrs
        if not where_clause:
            # TODO: support entity_id filter with custom where clause
            where_clause = "where entity_id = '{}'".format(entity_id) if entity_id else ""
        self.cursor.execute("select {} from {} {}".format(select_clause, self.TABLE_NAME, where_clause))

        res = self.cursor.fetchall()
        col_names = [x[0] for x in self.cursor.description]
        return list(self.translate_to_ngsi(res, col_names))


    def average(self, attr_name, entity_id=None):
        select_clause = "avg({})".format(attr_name)
        where_clause = "where entity_id = '{}'".format(entity_id) if entity_id else ""
        self.cursor.execute("select {} from {} {}".format(select_clause, self.TABLE_NAME, where_clause))
        avg = self.cursor.fetchone()[0]
        return avg
