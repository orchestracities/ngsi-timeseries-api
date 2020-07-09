from contextlib import contextmanager
import pg8000
from translators import sql_translator
from translators.sql_translator import NGSI_ISO8601, NGSI_DATETIME, \
    NGSI_GEOJSON, NGSI_TEXT, NGSI_STRUCTURED_VALUE, TIME_INDEX, \
    METADATA_TABLE_NAME, FIWARE_SERVICEPATH, TENANT_PREFIX
import geocoding.geojson.wktcodec
from geocoding.slf.geotypes import *
import geocoding.slf.wktcodec
from utils.cfgreader import *

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
        r = EnvReader(env, log=logging.getLogger(__name__).info)
        self.host = r.read(StrVar('POSTGRES_HOST', self.host))
        self.port = r.read(IntVar('POSTGRES_PORT', self.port))
        self.use_ssl = r.read(BoolVar('POSTGRES_USE_SSL', self.use_ssl))
        self.db_name = r.read(StrVar('POSTGRES_DB_NAME', self.db_name))
        self.db_user = r.read(StrVar('POSTGRES_DB_USER', self.db_user))
        self.db_pass = r.read(StrVar('POSTGRES_DB_PASS', self.db_pass,
                                     mask_value=True))


class PostgresTranslator(sql_translator.SQLTranslator):

    NGSI_TO_SQL = NGSI_TO_SQL

    def __init__(self, conn_data=PostgresConnectionData()):
        super(PostgresTranslator, self).__init__(
            conn_data.host, conn_data.port, conn_data.db_name)
        self.logger = logging.getLogger(__name__)
        self.db_user = conn_data.db_user
        self.db_pass = conn_data.db_pass
        self.ssl = {} if conn_data.use_ssl else None
        self.conn = None
        self.cursor = None

    def setup(self):
        pg8000.paramstyle = "qmark"
        self.conn = pg8000.connect(host=self.host, port=self.port, ssl_context=self.ssl,
                                   database=self.db_name,
                                   user=self.db_user, password=self.db_pass)
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

    def dispose(self):
        self.cursor.close()
        self.conn.close()

    @staticmethod
    def _svc_to_schema_name(fiware_service):
        if fiware_service:
            return '"{}{}"'.format(TENANT_PREFIX, fiware_service.lower())

    def _compute_type(self, attr_t, attr):
        return NGSI_TO_SQL[attr_t]

    def _prepare_data_table(self, table_name, table, fiware_service):
        schema = self._svc_to_schema_name(fiware_service)
        if schema:
            stmt = "create schema if not exists {}".format(schema)
            self.cursor.execute(stmt)

        # NOTE. Postgres identifiers (like column and table names) become case
        # sensitive when quoted like we do below in the CREATE TABLE statement.
        columns = ', '.join('"{}" {}'.format(cn.lower(), ct)
                            for cn, ct in table.items())
        stmt = "create table if not exists {} ({})".format(table_name, columns)
        self.cursor.execute(stmt)

        stmt = "select create_hypertable('{}', '{}', if_not_exists => true)" \
            .format(table_name, self.TIME_INDEX_NAME)
        self.cursor.execute(stmt)

        alt_cols = ', '.join('add column if not exists "{}" {}'
                             .format(cn.lower(), ct)
                             for cn, ct in table.items())
        stmt = "alter table {} {};".format(table_name, alt_cols)
        self.cursor.execute(stmt)

        ix_name = '"ix_{}_eid_and_tx"'.format(table_name.replace('"', ''))
        stmt = f"create index if not exists {ix_name} " +\
               f"on {table_name} (entity_id, {self.TIME_INDEX_NAME} desc)"
        self.cursor.execute(stmt)

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
                    mapped_type = table[cn]
                    ngsi_value = e[cn]['value']

                    if SlfGeometry.is_ngsi_slf_attr(e[cn]):
                        ast = SlfGeometry.build_from_ngsi_dict(e[cn])
                        mapped_value = geocoding.slf.wktcodec.encode_as_wkt(ast)
                    elif mapped_type == NGSI_TO_SQL[NGSI_GEOJSON]:
                        mapped_value = geocoding.geojson.wktcodec.encode_as_wkt(
                            ngsi_value)
                    elif mapped_type == NGSI_TO_SQL[NGSI_STRUCTURED_VALUE]:
                        mapped_value = pg8000.PGJsonb(ngsi_value)
                    elif mapped_type == NGSI_TO_SQL[NGSI_TEXT]:
                        mapped_value = str(ngsi_value)
                    elif mapped_type == PG_JSON_ARRAY:
                        mapped_value = pg8000.PGJsonb(ngsi_value)
                    else:
                        mapped_value = ngsi_value

                    values.append(mapped_value)
                except KeyError:
                    # this entity update does not have a value for the column
                    # so use None which will be inserted as NULL to the db.
                    values.append(None)
        return values

    @staticmethod
    def _to_db_ngsi_structured_value(data: dict) -> pg8000.PGJsonb:
        return pg8000.PGJsonb(data)

    def _should_insert_original_entities(self, insert_error: Exception) -> bool:
        return isinstance(insert_error, pg8000.ProgrammingError)

    def _create_metadata_table(self):
        stmt = "create table if not exists {} " \
               "(table_name text primary key, entity_attrs jsonb)"
        op = stmt.format(METADATA_TABLE_NAME)
        self.cursor.execute(op)

    def _store_medatata(self, table_name, persisted_metadata):
        stmt = "insert into {} (table_name, entity_attrs) values (?, ?) " \
               "on conflict (table_name) " \
               "do update set entity_attrs = ?"
        stmt = stmt.format(METADATA_TABLE_NAME)
        entity_attrs_value = pg8000.PGJsonb(persisted_metadata)
        self.cursor.execute(stmt, (table_name, entity_attrs_value,
                                   entity_attrs_value))

    def _get_geo_clause(self, geo_query):
        #TODO implement geo clause
        return ""

@contextmanager
def postgres_translator_instance():
    conn_data = PostgresConnectionData()
    conn_data.read_env()
    with PostgresTranslator(conn_data) as trans:
        yield trans
