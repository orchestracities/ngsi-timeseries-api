import json
import os
from contextlib import contextmanager
from crate import client
from crate.client import exceptions
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Sequence

from geocoding.slf.querytypes import SlfQuery
from translators import sql_translator
from translators.errors import CrateErrorAnalyzer
from translators.sql_translator import NGSI_ISO8601, NGSI_DATETIME, \
    NGSI_GEOJSON, NGSI_GEOPOINT, NGSI_TEXT, NGSI_STRUCTURED_VALUE, \
    NGSI_LD_GEOMETRY, TIME_INDEX, METADATA_TABLE_NAME, FIWARE_SERVICEPATH
import logging
from .crate_geo_query import from_ngsi_query
from utils.cfgreader import EnvReader, StrVar, IntVar, FloatVar
from utils.connection_manager import ConnectionManager

# CRATE TYPES
# https://crate.io/docs/crate/reference/en/latest/general/ddl/data-types.html
CRATE_ARRAY_STR = 'array(string)'

# Translation
NGSI_TO_SQL = {
    "Array": CRATE_ARRAY_STR,  # TODO #36: Support numeric arrays
    "Boolean": 'boolean',
    NGSI_ISO8601: 'timestamptz',
    NGSI_DATETIME: 'timestamptz',
    "Integer": 'bigint',
    NGSI_GEOJSON: 'geo_shape',
    NGSI_LD_GEOMETRY: 'geo_shape',
    NGSI_GEOPOINT: 'geo_point',
    "Number": 'real',
    NGSI_TEXT: 'text',
    NGSI_STRUCTURED_VALUE: 'object',
    TIME_INDEX: 'timestamptz'
}

CRATE_TO_NGSI = dict((v, k) for (k, v) in NGSI_TO_SQL.items())
CRATE_TO_NGSI['string_array'] = 'Array'

CRATE_HOST_ENV_VAR = 'CRATE_HOST'
CRATE_PORT_ENV_VAR = 'CRATE_PORT'
CRATE_DB_NAME_ENV_VAR = 'CRATE_DB_NAME'
CRATE_DB_USER_ENV_VAR = 'CRATE_DB_USER'
CRATE_DB_PASS_ENV_VAR = 'CRATE_DB_PASS'


class CrateConnectionData:

    def __init__(self, host='0.0.0.0', port=4200,
                 db_user='crate', db_pass=''):
        self.host = host
        self.port = port
        self.db_name = "ngsi-tsdb"
        self.db_user = db_user
        self.db_pass = db_pass
        self.backoff_factor = 0.0
        self.active_shards = '1'

    def read_env(self, env: dict = os.environ):
        r = EnvReader(env, log=logging.getLogger(__name__).debug)
        self.host = r.read(StrVar(CRATE_HOST_ENV_VAR, self.host))
        self.port = r.read(IntVar(CRATE_PORT_ENV_VAR, self.port))
        self.db_user = r.read(StrVar(CRATE_DB_USER_ENV_VAR, self.db_user))
        self.db_pass = r.read(StrVar(CRATE_DB_PASS_ENV_VAR, self.db_pass,
                                     mask_value=True))
        # Added backoff_factor for retry interval between attempt of
        # consecutive retries
        self.backoff_factor = r.read(FloatVar('CRATE_BACKOFF_FACTOR', 0.0))
        self.active_shards = r.read(StrVar('CRATE_WAIT_ACTIVE_SHARDS', '1'))


class CrateTranslator(sql_translator.SQLTranslator):
    NGSI_TO_SQL = NGSI_TO_SQL

    def __init__(self, conn_data=CrateConnectionData()):
        super(CrateTranslator, self).__init__(
            conn_data.host, conn_data.port, conn_data.db_name)
        self.logger = logging.getLogger(__name__)
        self.username = conn_data.db_user
        self.password = conn_data.db_pass
        self.backoff_factor = conn_data.backoff_factor
        self.active_shards = conn_data.active_shards
        self.ccm = None
        self.connection = None
        self.cursor = None
        self.dbCacheName = 'crate'

    def setup(self):
        url = "{}:{}".format(self.host, self.port)
        self.ccm = ConnectionManager()
        self.connection = self.ccm.get_connection('crate')
        if self.connection is None:
            try:
                self.connection = client.connect(
                    [url],
                    error_trace=True,
                    backoff_factor=self.backoff_factor,
                    username=self.username,
                    password=self.password)
                self.ccm.set_connection('crate', self.connection)
            except Exception as e:
                self.logger.warning(str(e), exc_info=True)
                raise e

        self.cursor = self.connection.cursor()
        # TODO this reduce queries to crate,
        # but only within a single API call to QUANTUMLEAP
        # we need to think if we want to cache this information
        # and save few msec for evey API call
        self.db_version = self.get_db_version()

        major = int(self.db_version.split('.')[0])
        if major < 4:
            logging.error("CRATE 4.x is the minimal version supported")
            raise Exception("Unsupported CrateDB version")

    def dispose(self):
        super(CrateTranslator, self).dispose()
        self.cursor.close()

    def dispose_connection(self):
        self.cursor.close()
        self.ccm.reset_connection('crate')

    def sql_error_handler(self, exception):
        analyzer = CrateErrorAnalyzer(exception)
        if analyzer.is_aggregation_error():
            return "AggrMethod cannot be applied"
        if analyzer.is_transient_error():
            self.ccm.reset_connection('crate')
            self.setup()

    def get_db_version(self):
        stmt = "select version['number'] from sys.nodes"
        res = self._execute_query_via_cache(self.dbCacheName,
                                            "dbversion",
                                            stmt, None, 6000)
        return res[0][0]

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

    @staticmethod
    def _ngsi_geojson_to_db(attr):
        return attr['value']

    @staticmethod
    def _ngsi_slf_to_db(attr):
        if attr['type'] == 'geo:point':
            lat, lon = attr['value'].split(',')
            return [float(lon), float(lat)]

    @staticmethod
    def _ngsi_structured_to_db(attr):
        attr_v = attr.get('value', None)
        if isinstance(attr_v, dict):
            return attr_v
        logging.warning('{} cannot be cast to {} replaced with None'.format(
            attr.get('value', None), attr.get('type', None)))
        return None

    @staticmethod
    def _ngsi_array_to_db(attr):
        attr_v = attr.get('value', None)
        if isinstance(attr_v, list):
            return attr_v
        logging.warning('{} cannot be cast to {} replaced with None'.format(
            attr.get('value', None), attr.get('type', None)))
        return None

    @staticmethod
    def _ngsi_default_to_db(attr):
        return attr.get('value', None)

    def _create_data_table(self, table_name, table, fiware_service):
        columns = ', '.join('"{}" {}'.format(cn.lower(), ct)
                            for cn, ct in table.items())
        stmt = "create table if not exists {} ({}) with " \
               "(\"number_of_replicas\" = '2-all', " \
               "\"column_policy\" = 'strict', " \
               "\"write.wait_for_active_shards\" = '{}'" \
               ")".format(table_name, columns, self.active_shards)
        self.cursor.execute(stmt)

    def _update_data_table(self, table_name, new_columns, fiware_service):
        # crate allows to add only one column for alter command!
        for cn in new_columns:
            alt_cols = 'add column "{}" {}'.format(cn.lower(), new_columns[cn])
            stmt = "alter table {} {};".format(table_name, alt_cols)
            self.cursor.execute(stmt)

    def _should_insert_original_entities(self,
                                         insert_error: Exception) -> bool:
        return isinstance(insert_error, Exception)

    def _build_original_data_value(self, entity: dict,
                                   insert_error: Exception = None,
                                   failed_batch_id: str = None) -> Any:
        value = {
            'data': json.dumps(entity)
        }
        if failed_batch_id:
            value['failedBatchID'] = failed_batch_id
        if insert_error:
            value['error'] = repr(insert_error)

        return self._to_db_ngsi_structured_value(value)

    def _create_metadata_table(self):
        stmt = "create table if not exists {} " \
               "(table_name string primary key, entity_attrs object) " \
               "with (" \
               "number_of_replicas = '2-all', " \
               "column_policy = 'dynamic')"
        op = stmt.format(METADATA_TABLE_NAME)
        self.cursor.execute(op)

    def _store_metadata(self, table_name, persisted_metadata):
        stmt = "insert into {} (table_name, entity_attrs) values (?,?) " \
            "on conflict(table_name) " \
            "DO UPDATE SET entity_attrs = excluded.entity_attrs"
        stmt = stmt.format(METADATA_TABLE_NAME)
        self.cursor.execute(stmt, (table_name, persisted_metadata))

    def _compute_db_specific_type(self, attr_t, attr):
        """
        Github issue 44: Disable indexing for long string
        """
        crate_t = self.NGSI_TO_SQL[attr_t]
        if attr_t == NGSI_TEXT:
            attr_v = attr.get('value', '')
            is_long = attr_v is not None and isinstance(attr_v, str) \
                and len(attr_v) > 32765
            if is_long:
                crate_t += ' INDEX OFF STORAGE WITH (columnstore = false)'
        return crate_t

    def _get_geo_clause(self, geo_query: SlfQuery = None) -> Optional[str]:
        return from_ngsi_query(geo_query)

    @staticmethod
    def _column_names_from_query_meta(cursor_description: Sequence) -> [str]:
        return [x[0] for x in cursor_description]

    @staticmethod
    def _get_isoformat(ms_since_epoch: Optional[int]) -> str:
        """
        :param ms_since_epoch:
            As stated in CrateDB docs: Timestamps are always returned as long
            values (ms from epoch).
        :return: str
            The equivalent datetime in ISO 8601.
        """
        if ms_since_epoch is None:
            return 'NULL'
        d = timedelta(milliseconds=ms_since_epoch)
        utc = datetime(1970, 1, 1, 0, 0, 0, 0, timezone.utc) + d
        return utc.isoformat(timespec='milliseconds')

    def _db_value_to_ngsi(self, db_value: Any, ngsi_type: str) -> Any:
        if db_value is None:
            return None

        # CrateDBs and NGSI use different geo:point coordinates order.
        if ngsi_type == NGSI_GEOPOINT:
            lon, lat = db_value
            return "{}, {}".format(lat, lon)

        if ngsi_type in (NGSI_DATETIME, NGSI_ISO8601):
            try:
                v = self._get_isoformat(db_value)
            except Exception as e:
                # There is a type mismatch.
                logging.warning("Column '{}' type is not TIMESTAMP".format(k))
            return v

        return db_value


@contextmanager
def crate_translator_instance():
    conn_data = CrateConnectionData()
    conn_data.read_env()
    with CrateTranslator(conn_data) as trans:
        yield trans
