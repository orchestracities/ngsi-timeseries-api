from contextlib import contextmanager
from crate import client
from crate.client import exceptions
from datetime import datetime
from translators import sql_translator
from translators.sql_translator import NGSI_ISO8601, NGSI_DATETIME, \
    NGSI_GEOJSON, NGSI_GEOPOINT, NGSI_TEXT, NGSI_STRUCTURED_VALUE, TIME_INDEX, \
    METADATA_TABLE_NAME, FIWARE_SERVICEPATH
import logging
from .crate_geo_query import from_ngsi_query
from utils.cfgreader import EnvReader, StrVar, IntVar


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

    def _should_insert_original_entities(self, insert_error: Exception) -> bool:
        return isinstance(insert_error, exceptions.ProgrammingError)

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
    r = EnvReader(log=logging.getLogger(__name__).info)
    db_host = r.read(StrVar('CRATE_HOST', 'crate'))
    db_port = r.read(IntVar('CRATE_PORT', 4200))
    db_name = "ngsi-tsdb"

    with CrateTranslator(db_host, db_port, db_name) as trans:
        yield trans
