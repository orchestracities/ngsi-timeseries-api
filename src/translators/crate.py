from contextlib import contextmanager
from crate import client
from crate.client.exceptions import ProgrammingError
from datetime import datetime, timedelta
from exceptions.exceptions import AmbiguousNGSIIdError
from translators import base_translator
from utils.common import iter_entity_attrs
import logging
import os
import statistics

# NGSI TYPES
# Based on Orion output because official docs don't say much about these :(
NGSI_DATETIME = 'DateTime'
NGSI_ID = 'id'
NGSI_ISO8601 = 'ISO8601'
NGSI_STRUCTURED_VALUE = 'StructuredValue'
NGSI_TEXT = 'Text'
NGSI_TYPE = 'type'

# CRATE TYPES
# https://crate.io/docs/crate/reference/en/latest/general/ddl/data-types.html
CRATE_ARRAY_STR = 'array(string)'

# Translation
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

# QUANTUMLEAP Internals
# A table to store the configuration and metadata of each entity type.
METADATA_TABLE_NAME = "md_ets_metadata"
FIWARE_SERVICEPATH = 'fiware_servicepath'
TENANT_PREFIX = 'mt'
TYPE_PREFIX = 'et'


class CrateTranslator(base_translator.BaseTranslator):

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
        Refreshing ensures a query after an insert retrieves the inserted data.
        :param entity_types: list(str) list of entity types whose tables will be
         refreshed
        """
        table_names = [self._et2tn(et, fiware_service) for et in entity_types]
        table_names.append(METADATA_TABLE_NAME)
        self.cursor.execute("refresh table {}".format(','.join(table_names)))


    def get_db_version(self):
        self.cursor.execute("select version['number'] from sys.nodes")
        return self.cursor.fetchall()[0][0]


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
        utc = datetime(1970, 1, 1, 0, 0, 0, 0) + d
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
        https://crate.io/docs/crate/reference/en/latest/sql/general/lexical-structure.html#key-words-and-identifiers
        ), both schema and table name are prefixed.
        """
        et = "{}{}".format(TYPE_PREFIX, entity_type.lower())
        if fiware_service:
            return "{}{}.{}".format(TENANT_PREFIX, fiware_service.lower(), et)
        return et


    def _ea2cn(self, entity_attr):
        """
        Entity Attr to Column Name.

        To create a column name out of an entity attribute, note the naming
        restrictions in crate.
        https://crate.io/docs/crate/reference/en/latest/general/ddl/create-table.html#naming-restrictions

        :return: column name
        """
        # GH Issue #64: prefix attributes with ea_.
        # This will break users connecting to db directly.
        # Implement when that becomes a real problem.
        return "{}".format(entity_attr.lower())


    def insert(self, entities, fiware_service=None, fiware_servicepath=None):
        if not isinstance(entities, list):
            msg = "Entities expected to be of type list, but got {}"
            raise TypeError(msg.format(type(entities)))

        entities_by_type = {}
        for e in entities:
            entities_by_type.setdefault(e['type'], []).append(e)

        res = None
        for et in entities_by_type.keys():
            res = self._insert_entities_of_type(et,
                                                entities_by_type[et],
                                                fiware_service,
                                                fiware_servicepath)
        return res


    def _insert_entities_of_type(self,
                                 entity_type,
                                 entities,
                                 fiware_service=None,
                                 fiware_servicepath=None):
        # All entities must be of the same type and have a time index
        for e in entities:
            if e[NGSI_TYPE] != entity_type:
                msg = "Entity {} is not of type {}."
                raise ValueError(msg.format(e[NGSI_ID], entity_type))

            if self.TIME_INDEX_NAME not in e:
                import warnings
                msg = "Translating entity without TIME_INDEX. " \
                      "It should have been inserted by the 'Reporter'. {}"
                warnings.warn(msg.format(e))
                e[self.TIME_INDEX_NAME] = datetime.now().isoformat()

        # Define column types
        # {column_name -> crate_column_type}
        table = {
            'entity_id': NGSI_TO_CRATE['Text'],
            'entity_type': NGSI_TO_CRATE['Text'],
        }

        # Preserve original attr names and types
        # {column_name -> (attr_name, attr_type)}
        original_attrs = {
            'entity_type': (NGSI_TYPE, NGSI_TEXT),
            'entity_id': (NGSI_ID, NGSI_TEXT),
            self.TIME_INDEX_NAME: (self.TIME_INDEX_NAME, NGSI_DATETIME),
        }

        for e in entities:
            for attr in iter_entity_attrs(e):
                if attr == self.TIME_INDEX_NAME:
                    table[self.TIME_INDEX_NAME] = NGSI_TO_CRATE[NGSI_DATETIME]
                    continue

                col = self._ea2cn(attr)

                if isinstance(e[attr], dict) and 'type' in e[attr]:
                    attr_t = e[attr]['type']
                else:
                    # Won't guess the type if used did't specify the type.
                    attr_t = NGSI_TEXT

                original_attrs[col] = (attr, attr_t)

                if attr_t not in NGSI_TO_CRATE:
                    supported_types = ', '.join(NGSI_TO_CRATE.keys())
                    msg = ("'{}' is not a supported NGSI type. "
                           "Please use any of the following: {}. "
                           "Falling back to {}.")
                    self.logger.warning(msg.format(
                        attr_t, supported_types, NGSI_TEXT))

                    table[col] = NGSI_TO_CRATE[NGSI_TEXT]

                else:
                    # Github issue 44: Disable indexing for long string
                    db_version = self.get_db_version()
                    crate_t = _adjust_gh_44(attr_t, e[attr], db_version)

                    # Github issue 24: StructuredValue == object or array
                    is_list = isinstance(e[attr].get('value', None), list)
                    if attr_t == NGSI_STRUCTURED_VALUE and is_list:
                        crate_t = CRATE_ARRAY_STR

                    table[attr] = crate_t

        # Create/Update metadata table for this type
        table_name = self._et2tn(entity_type, fiware_service)
        self._update_metadata_table(table_name, original_attrs)

        # Create Data Table
        columns = ', '.join('{} {}'.format(cn, ct) for cn, ct in table.items())
        stmt = "create table if not exists {} ({}) with " \
               "(number_of_replicas = '2-all')".format(table_name, columns)
        self.cursor.execute(stmt)

        # Gather attribute values
        col_names = sorted(table.keys())
        col_names.append(FIWARE_SERVICEPATH)
        entries = []  # raw values in same order as column names
        for e in entities:
            values = self._preprocess_values(e, col_names, fiware_servicepath)
            entries.append(values)

        # Insert entities data
        p1 = table_name
        p2 = ', '.join(col_names)
        p3 = ','.join(['?'] * len(col_names))
        stmt = "insert into {} ({}) values ({})".format(p1, p2, p3)
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


    def _update_metadata_table(self, table_name, metadata):
        """
        This method creates the METADATA_TABLE_NAME (if not exists), which
        stores, for each table_name (entity type), a translation table (dict)
        mapping the column names (from entity attributes) to the corresponding
        attributes metadata such as original attribute names and NGSI types.

        If such table existed, this method updates it accordingly if required.
        Required means, either there was no metadata for that
        table_name or the new_metadata has new entries not present in
        persisted_metadata.

        :param table_name: unicode
            The name of the table whose metadata will be updated

        :param metadata: dict
            The dict mapping the matedata of each column. See original_attrs.
        """
        stmt = "create table if not exists {} " \
               "(table_name string primary key, entity_attrs object) " \
               "with (number_of_replicas = '2-all')"
        op = stmt.format(METADATA_TABLE_NAME)
        self.cursor.execute(op)

        if self.cursor.rowcount:
            # Table just created!
            persisted_metadata = {}
        else:
            # Bring translation table!
            stmt = "select entity_attrs from {} where table_name = '{}'"
            self.cursor.execute(stmt.format(METADATA_TABLE_NAME, table_name))

            # By design, one entry per table_name
            res = self.cursor.fetchall()
            persisted_metadata = res[0][0] if res else {}

        if metadata.keys() - persisted_metadata.keys():
            persisted_metadata.update(metadata)
            stmt = "insert into {} (table_name, entity_attrs) values (?,?) " \
               "on duplicate key update entity_attrs = values(entity_attrs)"
            stmt = stmt.format(METADATA_TABLE_NAME)
            self.cursor.execute(stmt, (table_name, persisted_metadata))


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
            entity_type = self._get_entity_type(entity_id, fiware_service)

            if not entity_type:
                return []

            if len(entity_type.split(',')) > 1:
                raise AmbiguousNGSIIdError(entity_id)

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
            entity_type = self._get_entity_type(entity_id, fiware_service)

            if not entity_type:
                return 0

            if len(entity_type.split(',')) > 1:
                raise AmbiguousNGSIIdError(entity_id)

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


    def _get_entity_type(self, entity_id, fiware_service):
        """
        Find the type of the given entity_id.
        :returns: unicode
            Empty value if there is no entity with such entity_id.
            Or just the entity_type of the given entity_id if unique.
            Or a comma-separated list of entity_types with at least one record
            with such entity_id.
        """
        # Filter using tenant information
        if fiware_service is None:
            wc = "where table_name NOT like '{}%.%'".format(TENANT_PREFIX)
        else:
            # See _et2tn
            prefix = "{}{}".format(TENANT_PREFIX, fiware_service.lower())
            wc = "where table_name like '{}.%'".format(prefix)

        stmt = "select distinct(table_name) from {} {}".format(
            METADATA_TABLE_NAME,
            wc
        )
        self.cursor.execute(stmt)
        all_types = [et[0] for et in self.cursor.fetchall()]

        matching_types = []
        for et in all_types:
            stmt = "select distinct(entity_type) from {} " \
                   "where entity_id = '{}'".format(et, entity_id)
            self.cursor.execute(stmt)
            types = [t[0] for t in self.cursor.fetchall()]
            matching_types.extend(types)

        return ','.join(matching_types)


def _adjust_gh_44(attr_t, attr, db_version):
    """
    Github issue 44: Disable indexing for long string
    """
    crate_t = NGSI_TO_CRATE[attr_t]
    if attr_t == NGSI_TEXT:
        is_long = len(attr.get('value', '')) > 32765
        if is_long:
            # Before Crate v2.3
            crate_t += ' INDEX OFF'

            # After Crate v2.3
            major = int(db_version.split('.')[0])
            minor = int(db_version.split('.')[1])
            if (major == 2 and minor >= 3) or major > 2:
                crate_t += ' STORAGE WITH (columnstore = false)'
    return crate_t


@contextmanager
def CrateTranslatorInstance():
    DB_HOST = os.environ.get('CRATE_HOST', 'crate')
    DB_PORT = 4200
    DB_NAME = "ngsi-tsdb"
    with CrateTranslator(DB_HOST, DB_PORT, DB_NAME) as trans:
        yield trans
