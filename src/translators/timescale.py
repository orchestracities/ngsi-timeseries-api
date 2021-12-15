from contextlib import contextmanager
from datetime import datetime, timezone
import pg8000
import json
from typing import Any, Callable, Sequence
import os
from translators import sql_translator
from translators.errors import PostgresErrorAnalyzer
from translators.sql_translator import NGSI_ISO8601, NGSI_DATETIME, \
    NGSI_LD_GEOMETRY, NGSI_GEOJSON, NGSI_TEXT, NGSI_STRUCTURED_VALUE, \
    TIME_INDEX, METADATA_TABLE_NAME, TENANT_PREFIX
from translators.timescale_geo_query import from_ngsi_query
import geocoding.geojson.wktcodec
from geocoding.slf.geotypes import *
import geocoding.slf.jsoncodec
from geocoding.slf.querytypes import SlfQuery
import geocoding.slf.wktcodec
from utils.cfgreader import *
from utils.connection_manager import ConnectionManager

# POSTGRES TYPES
PG_JSON_ARRAY = 'jsonb'

# Translation
NGSI_TO_SQL = {
    "Array": PG_JSON_ARRAY,  # NB array of str in Crate backend!
    "Boolean": 'boolean',
    NGSI_ISO8601: 'timestamp WITH TIME ZONE',
    NGSI_DATETIME: 'timestamp WITH TIME ZONE',
    "Integer": 'bigint',
    NGSI_GEOJSON: 'geometry',
    NGSI_LD_GEOMETRY: 'geometry',
    SlfPoint.ngsi_type(): 'geometry',
    SlfLine.ngsi_type(): 'geometry',
    SlfPolygon.ngsi_type(): 'geometry',
    SlfBox.ngsi_type(): 'geometry',
    "Number": 'float',
    NGSI_TEXT: 'text',
    NGSI_STRUCTURED_VALUE: 'jsonb',
    # hyper-table requires a non-null time index
    TIME_INDEX: 'timestamp WITH TIME ZONE NOT NULL'
}

POSTGRES_HOST_ENV_VAR = 'POSTGRES_HOST'
POSTGRES_PORT_ENV_VAR = 'POSTGRES_PORT'
POSTGRES_USE_SSL_ENV_VAR = 'POSTGRES_USE_SSL'
POSTGRES_DB_NAME_ENV_VAR = 'POSTGRES_DB_NAME'
POSTGRES_DB_USER_ENV_VAR = 'POSTGRES_DB_USER'
POSTGRES_DB_PASS_ENV_VAR = 'POSTGRES_DB_PASS'


class PostgresConnectionData:

    def __init__(self, host='0.0.0.0', port=5432, use_ssl=False,
                 db_name='quantumleap',
                 db_user='quantumleap', db_pass='*'):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.db_name = db_name
        self.db_user = db_user
        self.db_pass = db_pass

    def read_env(self, env: dict = os.environ):
        r = EnvReader(env, log=logging.getLogger(__name__).debug)
        self.host = r.read(StrVar(POSTGRES_HOST_ENV_VAR, self.host))
        self.port = r.read(IntVar(POSTGRES_PORT_ENV_VAR, self.port))
        self.use_ssl = r.read(BoolVar(POSTGRES_USE_SSL_ENV_VAR, self.use_ssl))
        self.db_name = r.read(StrVar(POSTGRES_DB_NAME_ENV_VAR, self.db_name))
        self.db_user = r.read(StrVar(POSTGRES_DB_USER_ENV_VAR, self.db_user))
        self.db_pass = r.read(StrVar(POSTGRES_DB_PASS_ENV_VAR, self.db_pass,
                                     mask_value=True))


def _encode_to_json_string(data: dict or list) -> str:
    return json.dumps(data)


class PostgresTranslator(sql_translator.SQLTranslator):
    NGSI_TO_SQL = NGSI_TO_SQL

    def __init__(self, conn_data=PostgresConnectionData()):
        super(PostgresTranslator, self).__init__(
            conn_data.host, conn_data.port, conn_data.db_name)
        self.logger = logging.getLogger(__name__)
        self.db_user = conn_data.db_user
        self.db_pass = conn_data.db_pass
        self.ssl = {} if conn_data.use_ssl else None
        self.ccm = None
        self.connection = None
        self.cursor = None
        self.dbCacheName = 'timescale'

    def setup(self):
        self.ccm = ConnectionManager()
        self.connection = self.ccm.get_connection('timescale')
        if self.connection is None:
            try:
                pg8000.paramstyle = "qmark"
                self.connection = pg8000.connect(
                    host=self.host,
                    port=self.port,
                    ssl_context=self.ssl,
                    database=self.db_name,
                    user=self.db_user,
                    password=self.db_pass)
                self.connection.autocommit = True
                self.ccm.set_connection('timescale', self.connection)
            except Exception as e:
                self.logger.warning(str(e), exc_info=True)
                raise e

        self.cursor = self.connection.cursor()

    def dispose(self):
        super(PostgresTranslator, self).dispose()
        self.cursor.close()

    def sql_error_handler(self, exception):
        analyzer = PostgresErrorAnalyzer(exception)
        if analyzer.is_aggregation_error():
            return "AggrMethod cannot be applied"
        if analyzer.is_transient_error():
            self.ccm.reset_connection('timescale')
            self.setup()

    def with_connection_guard(self, db_action: Callable):
        try:
            db_action()
        except Exception as e:
            self.sql_error_handler(e)
            logging.error(str(e), exc_info=True)

    def get_health(self):
        health = {}

        op = "SELECT * FROM information_schema.tables"
        health['time'] = datetime.utcnow().isoformat(timespec='milliseconds')
        try:
            self.cursor.execute(op)

        except Exception as e:
            msg = "{}".format(e)
            logging.debug(msg)
            health['status'] = 'fail'
            health['output'] = msg

        else:
            health['status'] = 'pass'

        return health

    @staticmethod
    def _svc_to_schema_name(fiware_service):
        if fiware_service:
            return '"{}{}"'.format(TENANT_PREFIX, fiware_service.lower())

    def _compute_db_specific_type(self, attr_t, attr):
        return NGSI_TO_SQL[attr_t]

    def _create_data_table(self, table_name, table, fiware_service):
        def do_create():
            schema = self._svc_to_schema_name(fiware_service)
            if schema:
                stmt = f"create schema if not exists {schema}"
                self.cursor.execute(stmt)

            # NOTE. Postgres identifiers (like column and table names) become
            # case sensitive when quoted like we do below in the CREATE TABLE
            # statement.
            columns = ', '.join('"{}" {}'.format(cn.lower(), ct)
                                for cn, ct in table.items())
            stmt = f"create table if not exists {table_name} ({columns})"
            self.cursor.execute(stmt)

            stmt = f"select create_hypertable('{table_name}', " + \
                   f"'{self.TIME_INDEX_NAME}', if_not_exists => true)"
            self.cursor.execute(stmt)

            alt_cols = ', '.join('add column if not exists "{}" {}'
                                 .format(cn.lower(), ct)
                                 for cn, ct in table.items())
            stmt = "alter table {} {};".format(table_name, alt_cols)
            self.cursor.execute(stmt)

            ix_name = '"ix_{}_eid_and_tx"'.format(table_name.replace('"', ''))
            stmt = f"create index if not exists {ix_name} " + \
                f"on {table_name} (entity_id, {self.TIME_INDEX_NAME} desc)"
            self.cursor.execute(stmt)

        self.with_connection_guard(do_create)

    def _update_data_table(self, table_name, new_columns, fiware_service):
        def do_update():
            alt_cols = ', '.join('add column if not exists "{}" {}'
                                 .format(cn.lower(), ct)
                                 for cn, ct in new_columns.items())
            stmt = "alter table {} {};".format(table_name, alt_cols)
            self.cursor.execute(stmt)

        self.with_connection_guard(do_update)

    @staticmethod
    def _ngsi_geojson_to_db(attr):
        return geocoding.geojson.wktcodec.encode_as_wkt(
            attr['value'], srid=4326)

    @staticmethod
    def _ngsi_slf_to_db(attr):
        ast = SlfGeometry.build_from_ngsi_dict(attr)
        return geocoding.slf.wktcodec.encode_as_wkt(ast, srid=4326)

    @staticmethod
    def _ngsi_structured_to_db(attr):
        attr_v = attr.get('value', None)
        if isinstance(attr_v, dict):
            return _encode_to_json_string(attr_v)
        logging.warning('{} cannot be cast to {} replaced with None'.format(
            attr.get('value', None), attr.get('type', None)))
        return None

    @staticmethod
    def _ngsi_array_to_db(attr):
        attr_v = attr.get('value', None)
        if isinstance(attr_v, list):
            return _encode_to_json_string(attr_v)
        logging.warning('{} cannot be cast to {} replaced with None'.format(
            attr.get('value', None), attr.get('type', None)))
        return None

    def _db_value_to_ngsi(self, db_value: Any, ngsi_type: str) -> Any:
        if db_value is None:
            return None

        if ngsi_type in (NGSI_DATETIME, NGSI_ISO8601):
            v = None
            try:
                v = self._get_isoformat(db_value)
            except Exception as e:
                # There is a type mismatch.
                logging.warning(f"Column type is not TIMESTAMP: {v}")
            return v

        if SlfGeometry.is_ngsi_slf_attr({'type': ngsi_type}):
            geo_json = geocoding.geojson.wktcodec.decode_wkb_hexstr(db_value)
            slf_geom = geocoding.slf.jsoncodec.decode(geo_json, ngsi_type)
            return slf_geom.to_ngsi_attribute()['value'] if slf_geom else None

        if ngsi_type == NGSI_GEOJSON or ngsi_type == NGSI_LD_GEOMETRY:
            return geocoding.geojson.wktcodec.decode_wkb_hexstr(db_value)

        return db_value

    # NOTE. Implicit conversions.
    # 1. JSON. NGSI struct values and arrays get inserted as `jsonb`. When
    # reading `jsonb` values back from the DB, pg8000 automatically converts
    # them to Python dictionaries and arrays, respectively.
    # 2. Basic types (int, float, boolean and text). They also get converted
    # back to their corresponding Python types.

    @staticmethod
    def _to_db_ngsi_structured_value(data: dict) -> str:
        return _encode_to_json_string(data)

    def _should_insert_original_entities(self,
                                         insert_error: Exception) -> bool:
        return isinstance(insert_error, pg8000.ProgrammingError)

    def _create_metadata_table(self):
        def do_create():
            stmt = "create table if not exists {} " \
                   "(table_name text primary key, entity_attrs jsonb)"
            op = stmt.format(METADATA_TABLE_NAME)
            self.cursor.execute(op)

        self.with_connection_guard(do_create)

    def _store_metadata(self, table_name, persisted_metadata):
        def do_store():
            stmt = "insert into {} (table_name, entity_attrs) values (?, ?)" \
                   " on conflict (table_name)" \
                   " do update set entity_attrs = ?"
            stmt = stmt.format(METADATA_TABLE_NAME)
            entity_attrs_value = _encode_to_json_string(persisted_metadata)
            self.cursor.execute(stmt, (table_name, entity_attrs_value,
                                       entity_attrs_value))

        self.with_connection_guard(do_store)

    def _get_geo_clause(self, geo_query: SlfQuery = None) -> Optional[str]:
        return from_ngsi_query(geo_query)

    @staticmethod
    def _col_name(column_description: List) -> str:
        name = column_description[0]
        if isinstance(name, bytes):
            name = name.decode('utf-8')
        return name

    @staticmethod
    def _column_names_from_query_meta(cursor_description: Sequence) -> [str]:
        return [PostgresTranslator._col_name(x) for x in cursor_description]

    @staticmethod
    def _get_isoformat(timestamp_with_timezone: Optional[datetime]) -> str:
        if timestamp_with_timezone is None:
            return 'NULL'
        utc = timestamp_with_timezone.astimezone(timezone.utc)
        return utc.isoformat(timespec='milliseconds')


@contextmanager
def postgres_translator_instance():
    conn_data = PostgresConnectionData()
    conn_data.read_env()
    with PostgresTranslator(conn_data) as trans:
        yield trans
