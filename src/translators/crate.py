from contextlib import contextmanager
from crate import client
from crate.client import exceptions
from datetime import datetime
from translators import sql_translator
from translators.sql_translator import NGSI_ISO8601, NGSI_DATETIME, \
    NGSI_GEOJSON, NGSI_GEOPOINT, NGSI_TEXT, NGSI_STRUCTURED_VALUE, TIME_INDEX, \
    METADATA_TABLE_NAME, FIWARE_SERVICEPATH
import logging
from utils.cfgreader import *
import os
from .crate_geo_query import from_ngsi_query

# CRATE TYPES
# https://crate.io/docs/crate/reference/en/latest/general/ddl/data-types.html
CRATE_ARRAY_STR = 'array(string)'


# Translation
NGSI_TO_SQL = {
    "Array": CRATE_ARRAY_STR,  # TODO #36: Support numeric arrays
    "Boolean": 'boolean',
# TODO since CRATEDB 4.0 timestamp is deprecated. Should be replaced with timestampz
# This means that to maintain both version, we will need a different mechanism
    NGSI_ISO8601: 'timestamp',
    NGSI_DATETIME: 'timestamp',
    "Integer": 'long',
    NGSI_GEOJSON: 'geo_shape',
    NGSI_GEOPOINT: 'geo_point',
    "Number": 'float',
    NGSI_TEXT: 'string',
    NGSI_STRUCTURED_VALUE: 'object',
    TIME_INDEX: 'timestamp'
}


CRATE_TO_NGSI = dict((v, k) for (k,v) in NGSI_TO_SQL.items())
CRATE_TO_NGSI['string_array'] = 'Array'


class CrateTranslator(sql_translator.SQLTranslator):


    NGSI_TO_SQL = NGSI_TO_SQL


    def __init__(self, host, port=4200, db_name="ngsi-tsdb"):
        super(CrateTranslator, self).__init__(host, port, db_name)
        self.logger = logging.getLogger(__name__)

    def setup(self):
        url = "{}:{}".format(self.host, self.port)
        self.conn = client.connect([url], error_trace=True)
        self.cursor = self.conn.cursor()
        # TODO this reduce queries to crate,
        # but only within a single API call to QUANTUMLEAP
        # we need to think if we want to cache this information
        # and save few msec for evey API call
        self.db_version = self.get_db_version()


    def dispose(self):
        self.cursor.close()
        self.conn.close()


    def get_db_version(self):
        self.cursor.execute("select version['number'] from sys.nodes")
        return self.cursor.fetchall()[0][0]


    def get_health(self):
        """
        Return a dict of the status of crate service.

        Checkout
        https://crate.io/docs/crate/reference/en/latest/admin/system-information.html#health
        """
        health = {}

        op = "select health from sys.health order by severity desc limit 1"
        health['time'] = datetime.utcnow().isoformat(timespec='milliseconds')
        try:
            self.cursor.execute(op)

        except exceptions.ConnectionError as e:
            msg = "{}".format(e)
            logging.debug(msg)
            health['status'] = 'fail'
            health['output'] = msg

        else:
            res = self.cursor.fetchall()
            if len(res) == 0 or res[0][0] in ('GREEN', 'YELLOW'):
                # (can be empty when no tables were created yet)
                health['status'] = 'pass'
            else:
                c = res[0][0]
                health['status'] = 'warn'
                msg = "Checkout sys.health in crateDB, you have a {} status."
                health['output'] = msg.format(c)

        return health


    def _preprocess_values(self, e, table, col_names, fiware_servicepath):
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
                except KeyError:
                    # this entity update does not have a value for the column so use None which will be inserted as NULL to the db.
                    values.append( None )
        return values

    def _prepare_data_table(self, table_name, table, fiware_service):
        columns = ', '.join('"{}" {}'.format(cn.lower(), ct)
                            for cn, ct in table.items())
        stmt = "create table if not exists {} ({}) with " \
               "(number_of_replicas = '2-all', column_policy = 'dynamic')".format(table_name, columns)
        self.cursor.execute(stmt)

    def _create_metadata_table(self):
        stmt = "create table if not exists {} " \
               "(table_name string primary key, entity_attrs object) " \
               "with (number_of_replicas = '2-all', column_policy = 'dynamic')"
        op = stmt.format(METADATA_TABLE_NAME)
        self.cursor.execute(op)

    def _store_medatata(self, table_name, persisted_metadata):
        major = int(self.db_version.split('.')[0])
        if (major <= 3):
            stmt = "insert into {} (table_name, entity_attrs) values (?,?) " \
                   "on duplicate key update entity_attrs = values(entity_attrs)"
        else:
            stmt = "insert into {} (table_name, entity_attrs) values (?,?) " \
                   "on conflict(table_name) DO UPDATE SET entity_attrs = excluded.entity_attrs"
            stmt = stmt.format(METADATA_TABLE_NAME)
            self.cursor.execute(stmt, (table_name, persisted_metadata))


    def _get_et_table_names(self, fiware_service=None):
        """
        Return the names of all the tables representing entity types.
        :return: list(unicode)
        """
        op = "select distinct table_name from {} ".format(METADATA_TABLE_NAME)
        if fiware_service:
            where = "where table_name ~* '\"{}{}\"[.].*'"
            op += where.format(TENANT_PREFIX, fiware_service.lower())

        try:
            self.cursor.execute(op)
        except exceptions.ProgrammingError as e:
            # Metadata table still not created
            msg = "Could not retrieve METADATA_TABLE. Empty database maybe?. {}"
            logging.debug(msg.format(e))
            return []
        return [r[0] for r in self.cursor.rows]


    def _get_select_clause(self, attr_names, aggr_method, aggr_period):
        if not attr_names:
            return '*'

        attrs = ['entity_type', 'entity_id']
        if aggr_method:
            if aggr_period:
                attrs.append(
                    "DATE_TRUNC('{}',{}) as {}".format(
                        aggr_period, self.TIME_INDEX_NAME, self.TIME_INDEX_NAME)
                )
            # TODO: https://github.com/smartsdk/ngsi-timeseries-api/issues/106
            m = '{}("{}") as "{}"'
            attrs.extend(m.format(aggr_method, a, a) for a in set(attr_names))

        else:
            attrs.append(self.TIME_INDEX_NAME)
            attrs.extend('"{}"'.format(a) for a in attr_names)

        select = ','.join(attrs)
        return select


    def _get_limit(self, limit, last_n,env: dict = os.environ):
        # https://crate.io/docs/crate/reference/en/latest/general/dql/selects.html#limits
        default_limit = 10000
        env_default = None
        r = EnvReader(env, log=logging.getLogger(__name__).info)
        env_default = r.read(IntVar("DEFAULT_LIMIT",env_default))
        if env_default:
            default_limit = env_default
        if limit is None or limit > default_limit:
            limit = default_limit

        if last_n is None:
            last_n = limit

        if limit < 1 or last_n < 1:
            raise NGSIUsageError("Limit and LastN should be >=1 and <= {"
                                 "}.".format(default_limit))

        return min(last_n, limit)


    def _get_where_clause(self, entity_ids, from_date, to_date, fiware_sp=None,
                          geo_query=None):
        clauses = []

        if entity_ids:
            ids = ",".join("'{}'".format(e) for e in entity_ids)
            clauses.append(" entity_id in ({}) ".format(ids))
        if from_date:
            clauses.append(" {} >= '{}'".format(self.TIME_INDEX_NAME,
                                                self._parse_date(from_date)))
        if to_date:
            clauses.append(" {} <= '{}'".format(self.TIME_INDEX_NAME, self._parse_date(to_date)))

        if fiware_sp:
            # Match prefix of fiware service path
            clauses.append(" "+FIWARE_SERVICEPATH+" ~* '"+fiware_sp+"($|/.*)'")
       else:
            stmt = "insert into {} (table_name, entity_attrs) values (?,?) " \
                   "on conflict(table_name) DO UPDATE SET entity_attrs = excluded.entity_attrs"
        stmt = stmt.format(METADATA_TABLE_NAME)
        self.cursor.execute(stmt, (table_name, persisted_metadata))


    def _compute_type(self, attr_t, attr):
        """
        Github issue 44: Disable indexing for long string
        """
        crate_t = self.NGSI_TO_SQL[attr_t]
        if attr_t == NGSI_TEXT:
            attr_v = attr.get('value', '')
            is_long = attr_v is not None and len(attr_v) > 32765
            if is_long:
                # Before Crate v2.3
                crate_t += ' INDEX OFF'

                # After Crate v2.3
                major = int(self.db_version.split('.')[0])
                minor = int(self.db_version.split('.')[1])
                if (major == 2 and minor >= 3) or major > 2:
                    crate_t += ' STORAGE WITH (columnstore = false)'
        return crate_t


    def _get_geo_clause(self, geo_query):
        return from_ngsi_query(geo_query)


@contextmanager
def CrateTranslatorInstance():
    DB_HOST = os.environ.get('CRATE_HOST', 'crate')
    DB_PORT = os.environ.get('CRATE_PORT', 4200)
    DB_NAME = "ngsi-tsdb"
    with CrateTranslator(DB_HOST, DB_PORT, DB_NAME) as trans:
        yield trans
