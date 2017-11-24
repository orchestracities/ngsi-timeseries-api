from crate import client
from datetime import datetime, timedelta
from translators.base_translator import BaseTranslator
from utils.common import iter_entity_attrs
import logging
import statistics


# NGSI TYPES: Not properly documented so this might change. Based on Orion
# output.
NGSI_ID = 'id'
NGSI_TYPE = 'type'
NGSI_TEXT = 'Text'
NGSI_DATETIME = 'DateTime'


# CRATE TYPES: https://crate.io/docs/reference/sql/data_types.html
NGSI_TO_CRATE = {
    "Array": 'array(string)',  # TODO #36: Support numeric arrays
    "Boolean": 'boolean',
    NGSI_DATETIME: 'timestamp',
    "Integer": 'long',
    "geo:json": 'geo_shape',
    "Number": 'float',
    NGSI_TEXT: 'string',
    "StructuredValue": 'object'
}
CRATE_TO_NGSI = dict((v, k) for (k,v) in NGSI_TO_CRATE.items())
CRATE_TO_NGSI['string_array'] = 'Array'


# A table to store the configuration and metadata of each entity type.
METADATA_TABLE_NAME = "md_ets_metadata"


class CrateTranslator(BaseTranslator):

    def __init__(self, host, port=4200, db_name="ngsi-tsdb"):
        super(CrateTranslator, self).__init__(host, port, db_name)
        self.logger = logging.getLogger(__name__)


    def setup(self):
        url = "{}:{}".format(self.host, self.port)
        self.conn = client.connect([url], error_trace=True)
        self.cursor = self.conn.cursor()


    def dispose(self):
        self.cursor.close()
        self.conn.close()


    def _refresh(self, entity_types):
        """
        Used for testing purposes only!
        :param entity_types: list(str) list of entity types whose tables will be
         refreshed
        """
        table_names = [self._et2tn(et) for et in entity_types]
        table_names.append(METADATA_TABLE_NAME)
        self.cursor.execute("refresh table {}".format(','.join(table_names)))


    def _get_isoformat(self, ms_since_epoch):
        """
        :param ms_since_epoch:
            As stated in CrateDB docs: Timestamps are always returned as long
            values (ms from epoch).
        :return: str
            The equivalent datetime in ISO 8601.
        """
        if ms_since_epoch is None:
            raise ValueError
        d = timedelta(milliseconds=ms_since_epoch)
        utc = datetime(1970,1,1,0,0,0,0) + d
        return utc.isoformat()


    def translate_to_ngsi(self, resultset, col_names, table_name):
        """
        :param resultset: list of query results for one entity_type
        :param col_names: list of columns affected in the query
        :param table_name:
        :return: iterable(NGSI Entity)
            Iterable over the translated NGSI entities.
        """
        stmt = "select entity_attrs from {} where table_name = '{}'".format(
            METADATA_TABLE_NAME, table_name)
        self.cursor.execute(stmt)
        res = self.cursor.fetchall()

        if len(res) != 1:
            msg = "Cannot have {} entries in table '{}' for PK '{}'".format(
                len(res), METADATA_TABLE_NAME, table_name)
            self.logger.error(msg)
        entity_attrs = res[0][0]

        for r in resultset:
            entity = {}
            for k, v in zip(col_names, r):
                original_name, original_type = entity_attrs[k]

                if original_name in (NGSI_TYPE, NGSI_ID):
                    entity[original_name] = v

                elif original_name == self.TIME_INDEX_NAME:
                    # TODO: This might not be valid NGSI.
                    # Should we include this time_index in the reply?.
                    entity[original_name] = self._get_isoformat(v)

                else:
                    entity[original_name] = {'value': v, 'type': original_type}
                    if original_type == NGSI_DATETIME and v:
                        entity[original_name]['value'] = self._get_isoformat(v)
            yield entity


    def _et2tn(self, entity_type):
        return "et{}".format(entity_type.lower())


    def insert(self, entities):
        if not isinstance(entities, list):
            msg = "Entities expected to be of type list, but got {}"
            raise TypeError(msg.format(type(entities)))

        tables = {}         # {table_name -> {column_name -> crate_column_type}}
        entities_by_tn = {}  # {table_name -> list(entities)}

        # Collect tables info
        for e in entities:
            tn = self._et2tn(e['type'])

            table = tables.setdefault(tn, {})
            entities_by_tn.setdefault(tn, []).append(e)

            if self.TIME_INDEX_NAME not in e:
                # Recall it's the reporter's job to ensure each entity comes
                # with a TIME_INDEX attribute.
                import warnings
                mgs = "Translating entity without TIME_INDEX. {}"
                warnings.warn(msg.format(e))

            # Intentionally avoid using 'id' and 'type' as a column names.
            # It's problematic for some dbs.
            table['entity_id'] = NGSI_TO_CRATE['Text']
            table['entity_type'] = NGSI_TO_CRATE['Text']
            for attr in iter_entity_attrs(e):
                if attr == self.TIME_INDEX_NAME:
                    table[self.TIME_INDEX_NAME] = NGSI_TO_CRATE['DateTime']
                else:
                    ngsi_t = e[attr]['type'] if 'type' in e[attr] else NGSI_TEXT
                    if ngsi_t not in NGSI_TO_CRATE:
                        msg = ("'{}' is not a supported NGSI type. "
                               "Please use any of the following: {}. "
                               "Falling back to {}.").format(
                            ngsi_t, ", ".join(NGSI_TO_CRATE.keys()), NGSI_TEXT)
                        self.logger.warning(msg)
                        # Keep the original type to be saved in the metadata
                        # table, but switch to TEXT for crate column.
                        table[attr] = ngsi_t
                    else:
                        crate_t = NGSI_TO_CRATE[ngsi_t]
                        table[attr] = crate_t

        persisted_metadata = self._process_metadata_table(tables.keys())
        new_metadata = {}

        # Create data tables
        for tn, table in tables.items():
            # Preserve original attr names and types
            original_attrs = {
                'entity_type': (NGSI_TYPE, NGSI_TEXT),
                'entity_id': (NGSI_ID, NGSI_TEXT),
            }
            for attr, t in table.items():
                if t not in CRATE_TO_NGSI:
                    original_attrs[attr.lower()] = (attr, t)
                    # Having persisted original types in metadata, weird types
                    # fall back to string for crate.
                    table[attr] = NGSI_TO_CRATE[NGSI_TEXT]
                else:
                    if attr not in ('entity_type', 'entity_id'):
                        original_attrs[attr.lower()] = (attr, CRATE_TO_NGSI[t])
            new_metadata[tn] = original_attrs

            # Now create data table
            columns = ', '.join('{} {}'.format(cn, ct) for cn, ct in table.items())
            stmt = "create table if not exists {} ({})".format(tn, columns)
            self.cursor.execute(stmt)

        # Update metadata if necessary
        self._update_metadata_table(
            tables.keys(), persisted_metadata, new_metadata)

        # Populate data tables
        for tn, entities in entities_by_tn.items():
            col_names = sorted(tables[tn].keys())

            entries = []  # raw values in same order as column names
            for e in entities:
                temp = e.copy()
                temp['entity_type'] = {'value': temp.pop('type')}
                temp['entity_id'] = {'value': temp.pop('id')}
                temp[self.TIME_INDEX_NAME] = {'value': temp[self.TIME_INDEX_NAME]}
                try:
                    values = tuple(temp[x]['value'] for x in col_names)
                except KeyError as e:
                    msg = ("Seems like not all entities of same type came "
                           "with the same set of attributes. {}").format(e)
                    raise NotImplementedError(msg)
                entries.append(values)

            stmt = "insert into {} ({}) values ({})".format(
                tn, ', '.join(col_names), ('?,' * len(col_names))[:-1])
            self.cursor.executemany(stmt, entries)

        return self.cursor


    def _process_metadata_table(self, table_names):
        """
        This method creates the METADATA_TABLE_NAME (if not exists). This table
        maps, for each table_name (entity type), a translation table (dict)
        mapping the column names (entity attributes) to the corresponding
        attributes metadata such as original attribute names and NGSI types.

        :param table_names: iterable(unicode)
            The names of the tables whose metadata you are interested in.

        :return: dict
            The content of METADATA_TABLE_NAME.
        """
        stmt = ("create table if not exists {} "
                "(table_name string primary key, entity_attrs object)")
        self.cursor.execute(stmt.format(METADATA_TABLE_NAME))
        if self.cursor.rowcount:  # i.e, table just created
            return {}

        # Bring all translation tables
        stmt = "select table_name, entity_attrs from {} where table_name in ({})".format(
            METADATA_TABLE_NAME, ','.join("'{}'".format(t) for t in table_names)
        )
        self.cursor.execute(stmt)
        persisted_metadata = dict({tn: ea for (tn, ea) in self.cursor.fetchall()})
        return persisted_metadata


    def _update_metadata_table(self, table_names, persisted_metadata,
                               new_metadata):
        """
        Update the metadata (attributes translation table) of each table_name
        in table_names if required.

        Required means, either there was no metadata for that table_name or the
        new_metadata has new entries not present in persisted_metadata.
        """
        for tn in table_names:
            if tn not in persisted_metadata or new_metadata[tn].keys() - persisted_metadata[tn].keys():
                persisted_metadata.setdefault(tn, {}).update(new_metadata[tn])
                stmt = "insert into {} (table_name, entity_attrs) values (?,?) " \
                   "on duplicate key update entity_attrs = values(entity_attrs)".format(METADATA_TABLE_NAME)
                self.cursor.execute(stmt, (tn, persisted_metadata[tn]))


    def _get_et_table_names(self):
        """
        Return the names of all the tables representing entity types.
        :return: list(unicode)
        """
        try:
            self.cursor.execute("select distinct table_name from {}".format(
                METADATA_TABLE_NAME))
        except client.exceptions.ProgrammingError as e:
            # Metadata table still not created
            mssg = "Could not retrieve METADATA_TABLE. Empty database maybe?. {}"
            logging.debug(msg.format(e))
            return []
        return [r[0] for r in self.cursor.rows]


    def query(self, attr_names=None, entity_type=None, entity_id=None,
              where_clause=None):
        if entity_id and not entity_type:
            msg = "For now you must specify entity_type when stating entity_id"
            raise NotImplementedError(msg)

        select_clause = "{}".format(attr_names[0]) if attr_names else "*"
        # TODO: support some attrs
        if not where_clause:
            # TODO: support entity_id filter with custom where clause
            if entity_id:
                where_clause = "where entity_id = '{}'".format(entity_id)
            else:
                where_clause = ''

        if entity_type:
            table_names = [self._et2tn(entity_type)]
        else:
            table_names = self._get_et_table_names()

        result = []
        for tn in table_names:
            op = "select {} from {} {} order by {}".format(
                select_clause, tn, where_clause, self.TIME_INDEX_NAME)
            self.cursor.execute(op)
            res = self.cursor.fetchall()
            col_names = [x[0] for x in self.cursor.description]
            entities = list(self.translate_to_ngsi(res, col_names, tn))
            result.extend(entities)

        return result


    def average(self, attr_name, entity_type=None, entity_id=None):
        if entity_id and not entity_type:
            msg = "For now you must specify entity_type when stating entity_id"
            raise NotImplementedError(msg)

        if entity_type:
            table_names = [self._et2tn(entity_type)]
        else:
            # The semantic correctness of this operation is up to the client.
            table_names = self._get_et_table_names()

        values = []
        for tn in table_names:
            select_clause = "avg({})".format(attr_name)
            if entity_id:
                where_clause = ("where entity_id = '%s'" % entity_id)
            else:
                where_clause = ''
            stmt = "select {} from {} {}".format(select_clause, tn, where_clause)
            self.cursor.execute(stmt)
            avg = self.cursor.fetchone()[0]
            values.append(avg)

        return statistics.mean(values)
