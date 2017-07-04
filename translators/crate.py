from crate import client
from datetime import datetime, timedelta
from translators.base_translator import BaseTranslator


# NGSI TYPES: Not properly documented so this might change. Based on experimenting with Orion.
# CRATE TYPES: https://crate.io/docs/reference/sql/data_types.html
NGSI_TO_CRATE = {
    "Text": 'string',
    "Number": 'float',
    "Integer": 'long',
    "Boolean": 'boolean',
    "DateTime": 'timestamp',
    "json:geo": 'geo_shape',
}
CRATE_TO_NGSI = dict((v, k) for (k,v) in NGSI_TO_CRATE.items())


class CrateTranslator(BaseTranslator):

    def __init__(self, host, port=4200, db_name="ngsi-tsdb"):
        super(CrateTranslator, self).__init__(host, port, db_name)

        self.table_name = 'notifications'
        self.table_columns = None  # name:type of columns for correct querying


    def setup(self):
        self.conn = client.connect(["{}:{}".format(self.host, self.port)], error_trace=True)
        self.cursor = self.conn.cursor()


    def dispose(self, testing=False):
        if testing:
            self.cursor.execute("DROP TABLE IF EXISTS {}".format(self.table_name))

        self.table_name = None
        self.table_columns = None

        self.cursor.close()
        self.conn.close()


    def create_table(self, entity):
        """
        :param entity: Entity used to derive table name (entity_type) and columns (all attrs of entity)
        :return: str. The name of the created table
        """
        if self.TIME_INDEX_NAME not in entity:
            import warnings
            warnings.warn("Translating entity without TIME_INDEX. {}".format(entity))

        name_type = {}
        e = entity.copy()
        e['entity_type'] = e.pop('type')
        e['entity_id'] = e.pop('id')

        for k, v in e.items():
            if k == self.TIME_INDEX_NAME:
                name_type[k] = NGSI_TO_CRATE['DateTime']
                continue

            if isinstance(v, dict):
                ngsi_t = v['type']
                crate_t = NGSI_TO_CRATE[ngsi_t]
            else:
                crate_t = 'string'

            name_type[k] = crate_t

        columns = ','.join('{} {}'.format(n, t) for n, t in name_type.items())
        cmd = "create table if not exists {} ( \
                        {})".format(self.table_name, columns)
        self.cursor.execute(cmd)
        return ','.join(str(c) for c in sorted(name_type.keys()))


    def refresh(self):
        self.cursor.execute("refresh table {}".format(self.table_name))


    def translate_from_ngsi(self, entities):
        for entity in entities:
            row = []
            # Keep order of definitive column names.
            e = entity.copy()
            e['entity_type'] = e.pop('type')
            e['entity_id'] = e.pop('id')
            for k in sorted(e.keys()):
                if isinstance(e[k], dict):
                    row.append(e[k]["value"])
                else:
                    # assert isinstance(e[k], str)
                    row.append(e[k])
            yield row


    def _get_isoformat(self, ms_since_epoch):
        """
        :param ms_since_epoch:
            As stated in CrateDB docs: Timestamps are always returned as long values (ms from epoch).
        :return: str
            The equivalent datetime in ISO 8601.
        """
        if ms_since_epoch is None:
            raise ValueError
        utc = datetime(1970, 1, 1, 0, 0, 0, 0) + timedelta(milliseconds=ms_since_epoch)
        return utc.isoformat()


    def translate_to_ngsi(self, resultset, keys):
        if self.table_columns is None:
            op = "select column_name, data_type from information_schema.columns where table_name = 'notifications'"
            self.cursor.execute(op)
            res = self.cursor.fetchall()
            self.table_columns = dict((k, v) for (k, v) in res)

        for r in resultset:
            entity = {}
            for k, v in zip(keys, r):
                if k == self.TIME_INDEX_NAME:
                    # TODO: This might not be valid NGSI. Should we include this? if so, shouldn't it have metadata?
                    entity[self.TIME_INDEX_NAME] = self._get_isoformat(v)
                else:
                    if k in ('entity_type', 'entity_id'):
                        entity[k] = v
                    else:
                        t = CRATE_TO_NGSI[self.table_columns[k]]
                        entity[k] = {'value': v, 'type': t}
                        if t == 'DateTime' and entity[k]['value']:
                            entity[k]['value'] = self._get_isoformat(entity[k]['value'])

            entity['type'] = entity.pop('entity_type')
            entity['id'] = entity.pop('entity_id')
            yield entity


    def insert(self, entities):
        if not isinstance(entities, list):
            raise TypeError("Entities expected to be of type list, but got {}".format(type(entities)))

        types = set([e['type'] for e in entities])
        if len(types) > 1:
            # TODO: verify if a notification can arrive with multiple entity types or not.
            # I.e, verify if this case is worth supporting.
            raise ValueError('Inserting multiple types at once not yet supported')

        col_names = self.create_table(entities[0])

        entries = list(self.translate_from_ngsi(entities))
        op = "insert into {} ({}) values ({})".format(self.table_name, col_names, ','.join('?'*len(entities[0])))

        self.cursor.executemany(op, entries)
        return self.cursor


    def query(self, attr_names=None, entity_id=None, where_clause=None):
        assert self.table_name is not None

        select_clause = "{}".format(attr_names[0]) if attr_names else "*"  # TODO: support some attrs
        if not where_clause:
            # TODO: support entity_id filter with custom where clause
            where_clause = "where entity_id = '{}'".format(entity_id) if entity_id else ''
        op = "select {} from {} {}".format(select_clause, self.table_name, where_clause)
        self.cursor.execute(op)

        res = self.cursor.fetchall()
        col_names = [x[0] for x in self.cursor.description]
        entities = list(self.translate_to_ngsi(res, col_names))
        return entities


    def average(self, attr_name, entity_id=None):
        assert self.table_name is not None

        select_clause = "avg({})".format(attr_name)
        where_clause = "where entity_id = '{}'".format(entity_id) if entity_id else ""
        self.cursor.execute("select {} from {} {}".format(select_clause, self.table_name, where_clause))
        avg = self.cursor.fetchone()[0]
        return avg
