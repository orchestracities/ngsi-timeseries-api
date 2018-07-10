from contextlib import contextmanager
from crate import client
from crate.client.exceptions import ProgrammingError
from datetime import datetime, timedelta
from translators.base_translator import BaseTranslator
from utils.common import iter_entity_attrs
import logging
import os
import statistics


# NGSI TYPES: Not properly documented so this might change. Based on Orion
# output.
NGSI_ID = 'id'
NGSI_TYPE = 'type'
NGSI_TEXT = 'Text'
NGSI_DATETIME = 'DateTime'
NGSI_STRUCTURED_VALUE = 'StructuredValue'
NGSI_ISO8601 = 'ISO8601'

CRATE_ARRAY_STR = 'array(string)'

# CRATE TYPES: https://crate.io/docs/reference/sql/data_types.html
NGSI_TO_CRATE = {
    "Array": CRATE_ARRAY_STR,  # TODO #36: Support numeric arrays
    "Boolean": 'boolean',
    NGSI_ISO8601: 'timestamp',
    NGSI_DATETIME: 'timestamp',
    "Integer": 'long',
    "geo:json": 'geo_shape',
    "geo:point": 'geo_point',
    "Number": 'float',
    NGSI_TEXT: 'string',
    NGSI_STRUCTURED_VALUE: 'object'
}
CRATE_TO_NGSI = dict((v, k) for (k,v) in NGSI_TO_CRATE.items())
CRATE_TO_NGSI['string_array'] = 'Array'


# A table to store the configuration and metadata of each entity type.
METADATA_TABLE_NAME = "md_ets_metadata"

FIWARE_SERVICEPATH = 'fiware_servicepath'
TENANT_PREFIX = 'mt'


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


    def _refresh(self, entity_types, fiware_service=None):
        """
        Used for testing purposes only!
        :param entity_types: list(str) list of entity types whose tables will be
         refreshed
        """
        table_names = [self._et2tn(et, fiware_service) for et in entity_types]
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
                if k not in entity_attrs:
                    continue

                original_name, original_type = entity_attrs[k]
                if original_name in (NGSI_TYPE, NGSI_ID):
                    entity[original_name] = v

                elif original_name == self.TIME_INDEX_NAME:
                    # TODO: This might not be valid NGSI.
                    # Should we include this time_index in the reply?.
                    entity[original_name] = self._get_isoformat(v)

                else:
                    entity[original_name] = {'value': v, 'type': original_type}
                    if original_type in (NGSI_DATETIME, NGSI_ISO8601) and v:
                        entity[original_name]['value'] = self._get_isoformat(v)

            self._postprocess_values(entity)
            yield entity


    def _et2tn(self, entity_type, fiware_service=None):
        """
        Return table name based on entity type.
        When specified, fiware_service will define the table schema.
        To avoid conflict with reserved words (
        https://crate.io/docs/crate/reference/en/latest/sql/general/lexical-structure.html#key-words-and-identifiers),
        both schema and table name are prefixed.
        """
        et = "et{}".format(entity_type.lower())
        if fiware_service:
            return "{}{}.{}".format(TENANT_PREFIX, fiware_service.lower(), et)
        return et


    def insert(self, entities, fiware_service=None, fiware_servicepath=None):
        if not isinstance(entities, list):
            msg = "Entities expected to be of type list, but got {}"
            raise TypeError(msg.format(type(entities)))

        tables = {}         # {table_name -> {column_name -> crate_column_type}}
        entities_by_tn = {}  # {table_name -> list(entities)}
        custom_columns = {}  # {table_name -> attr_name -> custom_column}

        # Collect tables info
        for e in entities:
            tn = self._et2tn(e['type'], fiware_service)

            table = tables.setdefault(tn, {})
            entities_by_tn.setdefault(tn, []).append(e)

            if self.TIME_INDEX_NAME not in e:
                import warnings
                msg = "Translating entity without TIME_INDEX. " \
                      "It should have been inserted by the 'Reporter'. {}"
                warnings.warn(msg.format(e))
                e[self.TIME_INDEX_NAME] = datetime.now().isoformat()

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
                        # Github issue 44: Disable indexing for long string
                        if ngsi_t == NGSI_TEXT and \
                           len(e[attr]['value']) > 32765:
                            custom_columns.setdefault(tn, {})[attr] = crate_t \
                              + ' INDEX OFF'

                        # Github issue 24: StructuredValue == object or array
                        if ngsi_t == NGSI_STRUCTURED_VALUE and \
                                isinstance(e[attr].get('value', None), list):
                                crate_t = CRATE_ARRAY_STR

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
                        if isinstance(e[attr], dict) and e[attr].get('type', None) == NGSI_ISO8601:
                            original_attrs[attr.lower()] = (attr, NGSI_ISO8601)
            new_metadata[tn] = original_attrs

            # Apply custom column modifiers
            for _attr_name, cc in custom_columns.setdefault(tn, {}).items():
                table[_attr_name] = cc

            # Now create data table
            columns = ', '.join('{} {}'.format(cn, ct) for cn, ct in table.items())
            stmt = "create table if not exists {} ({}) with " \
                   "(number_of_replicas = '2-all')".format(tn, columns)
            self.cursor.execute(stmt)

        # Update metadata if necessary
        self._update_metadata_table(
            tables.keys(), persisted_metadata, new_metadata)

        # Populate data tables
        for tn, entities in entities_by_tn.items():
            col_names = sorted(tables[tn].keys())
            col_names.append(FIWARE_SERVICEPATH)

            entries = []  # raw values in same order as column names
            for e in entities:
                values = self._preprocess_values(e,
                                                 col_names,
                                                 fiware_servicepath)
                entries.append(values)

            stmt = "insert into {} ({}) values ({})".format(
                tn, ', '.join(col_names), ('?,' * len(col_names))[:-1])
            self.cursor.executemany(stmt, entries)

        return self.cursor

    def _preprocess_values(self, e, col_names, fiware_servicepath):
        values = []
        for cn in col_names:
            if cn == 'entity_type':
                values.append(e['type'])
            elif cn == 'entity_id':
                values.append(e['id'])
            elif cn == self.TIME_INDEX_NAME:
                values.append(e[self.TIME_INDEX_NAME])
            elif cn == FIWARE_SERVICEPATH:
                values.append(fiware_servicepath or '')
            else:
                # Normal attributes
                try:
                    if 'type' in e[cn] and e[cn]['type'] == 'geo:point':
                        lat, lon = e[cn]['value'].split(',')
                        values.append([float(lon), float(lat)])
                    else:
                        values.append(e[cn]['value'])
                except KeyError as e:
                    msg = ("Seems like not all entities of same type came "
                           "with the same set of attributes. {}").format(e)
                    raise NotImplementedError(msg)
        return values

    def _postprocess_values(self, e):
        for attr in iter_entity_attrs(e):
            if 'type' in e[attr] and e[attr]['type'] == 'geo:point':
                lon, lat = e[attr]['value']
                e[attr]['value'] = "{}, {}".format(lat, lon)
        return e


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
                "(table_name string primary key, entity_attrs object) with "
                "(number_of_replicas = '2-all')")
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


    def _get_et_table_names(self, fiware_service=None):
        """
        Return the names of all the tables representing entity types.
        :return: list(unicode)
        """
        op = "select distinct table_name from {} ".format(METADATA_TABLE_NAME)
        if fiware_service:
            op += "where table_name ~* '{}{}[.].*'".format(TENANT_PREFIX,
                                                           fiware_service.lower())
        try:
            self.cursor.execute(op)
        except client.exceptions.ProgrammingError as e:
            # Metadata table still not created
            msg = "Could not retrieve METADATA_TABLE. Empty database maybe?. {}"
            logging.debug(msg.format(e))
            return []
        return [r[0] for r in self.cursor.rows]


    def _get_select_clause(self, attr_names, aggr_method):
        if attr_names:
            if aggr_method:
                attrs = ["{}({})".format(aggr_method, a) for a in attr_names]
            else:
                attrs = [self.TIME_INDEX_NAME]
                attrs.extend(str(a) for a in attr_names)
            select = ",".join(attrs)

        else:
            # aggr_method is ignored when no attribute is specified
            select = '*'
        return select


    def _get_limit(self, limit):
        # https://crate.io/docs/crate/reference/en/latest/general/dql/selects.html#limits
        default = 10000
        if not limit:
            return default
        limit = int(limit)
        if limit < 1:
            raise ValueError("Limit should be >=1 and <= 10000.")
        return min(default, limit)


    def _get_where_clause(self, entity_id, from_date, to_date, fiware_sp=None):
        clauses = []

        if entity_id:
            clauses.append(" entity_id = '{}' ".format(entity_id))
        if from_date:
            clauses.append(" {} >= '{}'".format(self.TIME_INDEX_NAME, from_date))
        if to_date:
            clauses.append(" {} <= '{}'".format(self.TIME_INDEX_NAME, to_date))

        if fiware_sp:
            # Match prefix of fiware service path
            clauses.append(" "+FIWARE_SERVICEPATH+" ~* '"+fiware_sp+"($|/.*)'")
        else:
            # Match prefix of fiware service path
            clauses.append(" "+FIWARE_SERVICEPATH+" = ''")

        where_clause = "where " + "and ".join(clauses)
        return where_clause


    def query(self,
              attr_names=None,
              entity_type=None,
              entity_id=None,
              where_clause=None,
              aggr_method=None,
              from_date=None,
              to_date=None,
              last_n=None,
              limit=10000,
              offset=0,
              fiware_service=None,
              fiware_servicepath=None):
        if entity_id and not entity_type:
            msg = "For now you must specify entity_type when stating entity_id"
            raise NotImplementedError(msg)

        select_clause = self._get_select_clause(attr_names, aggr_method)

        if not where_clause:
            where_clause = self._get_where_clause(entity_id,
                                                  from_date,
                                                  to_date,
                                                  fiware_servicepath)

        if aggr_method:
            order_by = "" if select_clause == "*" else "group by entity_id"
        else:
            order_by = "order by {} ASC".format(self.TIME_INDEX_NAME)

        if entity_type:
            table_names = [self._et2tn(entity_type, fiware_service)]
        else:
            table_names = self._get_et_table_names(fiware_service)

        limit = self._get_limit(limit)
        offset = max(0, offset)

        result = []
        for tn in table_names:
            op = "select {select_clause} " \
                 "from {tn} " \
                 "{where_clause} " \
                 "{order_by} " \
                 "limit {limit} offset {offset}".format(
                    select_clause=select_clause,
                    tn=tn,
                    where_clause=where_clause,
                    order_by=order_by,
                    limit=limit,
                    offset=offset,
                )
            try:
                self.cursor.execute(op)
            except ProgrammingError as e:
                # Reason 1: fiware_service_path column in legacy dbs.
                logging.debug("{}".format(e))
                entities = []
            else:
                res = self.cursor.fetchall()
                if aggr_method and attr_names:
                    col_names = attr_names
                else:
                    col_names = [x[0] for x in self.cursor.description]
                entities = list(self.translate_to_ngsi(res, col_names, tn))
            result.extend(entities)

        if last_n:
            # TODO: embed last_n in query to avoid waste.
            return result[-last_n:]
        return result

    # TODO: Remove this method (needs refactoring of the benchmark)
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


    def delete_entity(self, entity_id, entity_type=None, from_date=None,
                      to_date=None, fiware_service=None,
                      fiware_servicepath=None):
        if not entity_type:
            msg = "For now you must specify entity type"
            raise NotImplementedError(msg)

        # First delete entries from table
        table_name = self._et2tn(entity_type, fiware_service)
        where_clause = self._get_where_clause(entity_id,
                                              from_date,
                                              to_date,
                                              fiware_servicepath)
        op = "delete from {} {}".format(table_name, where_clause)

        try:
            self.cursor.execute(op)
        except ProgrammingError as e:
            logging.debug("{}".format(e))
            return 0

        return self.cursor.rowcount


    def delete_entities(self, entity_type, from_date=None, to_date=None,
                        fiware_service=None, fiware_servicepath=None):
        table_name = self._et2tn(entity_type, fiware_service)

        # Delete only requested range
        if from_date or to_date or fiware_servicepath:
            entity_id = None
            where_clause = self._get_where_clause(entity_id,
                                                  from_date,
                                                  to_date,
                                                  fiware_servicepath)
            op = "delete from {} {}".format(table_name, where_clause)
            try:
                self.cursor.execute(op)
            except ProgrammingError as e:
                logging.debug("{}".format(e))
                return 0
            return self.cursor.rowcount

        # Drop whole table
        try:
            self.cursor.execute("select count(*) from {}".format(table_name))
        except ProgrammingError as e:
            logging.debug("{}".format(e))
            return 0
        count = self.cursor.fetchone()[0]

        op = "drop table {}".format(table_name)
        try:
            self.cursor.execute(op)
        except ProgrammingError as e:
            logging.debug("{}".format(e))
            return 0

        # Delete entry from metadata table
        op = "delete from {} where table_name = '{}'".format(
            METADATA_TABLE_NAME, table_name
        )
        try:
            self.cursor.execute(op)
        except ProgrammingError as e:
            # What if this one fails and previous didn't?
            logging.debug("{}".format(e))

        return count


@contextmanager
def CrateTranslatorInstance():
    DB_HOST = os.environ.get('CRATE_HOST', 'crate')
    DB_PORT = 4200
    DB_NAME = "ngsi-tsdb"
    with CrateTranslator(DB_HOST, DB_PORT, DB_NAME) as trans:
        yield trans
