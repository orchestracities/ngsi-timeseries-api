from contextlib import contextmanager
from datetime import datetime
import pg8000

import geocoding.geojson.wktcodec
from geocoding.slf.geotypes import *
import geocoding.slf.wktcodec
from translators import base_translator
from utils.cfgreader import *
from utils.common import iter_entity_attrs


# TODO: Refactor this mess!
# I've applied my famed copy & pasta tech to cook up the lovely spaghetti
# code below. I started out by copying over the Crate translator code and
# then hacked it to pieces until it worked with Timescale. I've kept the
# same structure and even the original comments to make it easier to compare
# it to the original.
# I suggest we refactor both this and the Crate translator using something
# like SQLAlchemy if we want to keep the same approach of doing everything
# in Python, but this isn't exactly a good thing for performance---way too
# many calls on each insert! Perhaps we should come up with a more efficient
# design or at least consider stored procs.
# Anyhoo, for the time being...bless this mess!


# NGSI TYPES
# Based on Orion output because official docs don't say much about these :(
NGSI_DATETIME = 'DateTime'
NGSI_ID = 'id'
NGSI_GEOJSON = 'geo:json'
NGSI_ISO8601 = 'ISO8601'
NGSI_STRUCTURED_VALUE = 'StructuredValue'
NGSI_TEXT = 'Text'
NGSI_TYPE = 'type'

# POSTGRES TYPES
PG_JSON_ARRAY = 'jsonb'
# hyper-table requires a non-null time index
PG_TIME_INDEX = 'timestamp WITH TIME ZONE NOT NULL'


# Translation
NGSI_TO_PG = {
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
    NGSI_STRUCTURED_VALUE: 'jsonb'
}


# QUANTUMLEAP Internals
# A table to store the configuration and metadata of each entity type.
METADATA_TABLE_NAME = "md_ets_metadata"
FIWARE_SERVICEPATH = 'fiware_servicepath'
TENANT_PREFIX = 'mt'
TYPE_PREFIX = 'et'


class PostgresConnectionData:

    def __init__(self, host='timescale', port=5432, use_ssl=False,
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


class PostgresTranslator(base_translator.BaseTranslator):

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
        self.conn = pg8000.connect(host=self.host, port=self.port, ssl=self.ssl,
                                   database=self.db_name,
                                   user=self.db_user, password=self.db_pass)
        self.cursor = self.conn.cursor()

    def dispose(self):
        self.cursor.close()
        self.conn.close()

    @staticmethod
    def _svc_to_schema_name(fiware_service):
        if fiware_service:
            return '"{}{}"'.format(TENANT_PREFIX, fiware_service.lower())

    @staticmethod
    def _et2tn(entity_type, fiware_service=None):
        """
        Return table name based on entity type.
        When specified, fiware_service will define the table schema.
        To avoid conflict with reserved words (
        https://crate.io/docs/crate/reference/en/latest/sql/general/lexical-structure.html#key-words-and-identifiers
        ), both schema and table name are prefixed.
        """
        et = '"{}{}"'.format(TYPE_PREFIX, entity_type.lower())
        if fiware_service:
            return '"{}{}".{}'.format(TENANT_PREFIX, fiware_service.lower(), et)
        return et

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
                now_iso = datetime.now().isoformat(timespec='milliseconds')
                e[self.TIME_INDEX_NAME] = now_iso

        # Define column types
        # {column_name -> pg_column_type}
        table = {
            'entity_id': NGSI_TO_PG['Text'],
            'entity_type': NGSI_TO_PG['Text'],
            self.TIME_INDEX_NAME: PG_TIME_INDEX,
            FIWARE_SERVICEPATH: NGSI_TO_PG['Text']
        }

        # Preserve original attr names and types
        # {column_name -> (attr_name, attr_type)}
        original_attrs = {
            'entity_type': (NGSI_TYPE, NGSI_TEXT),
            'entity_id': (NGSI_ID, NGSI_TEXT),
            self.TIME_INDEX_NAME: (self.TIME_INDEX_NAME, NGSI_DATETIME)
        }

        for e in entities:
            for attr in iter_entity_attrs(e):
                if attr == self.TIME_INDEX_NAME:
                    continue

                if isinstance(e[attr], dict) and 'type' in e[attr]:
                    attr_t = e[attr]['type']
                else:
                    # Won't guess the type if used did't specify the type.
                    attr_t = NGSI_TEXT

                original_attrs[attr] = (attr, attr_t)

                if attr_t not in NGSI_TO_PG:
                    # if attribute is complex assume NGSI StructuredValue
                    if self._attr_is_structured(e[attr]):
                        table[attr] = NGSI_TO_PG[NGSI_STRUCTURED_VALUE]
                    else:
                        supported_types = ', '.join(NGSI_TO_PG.keys())
                        msg = ("'{}' is not a supported NGSI type. "
                               "Please use any of the following: {}. "
                               "Falling back to {}.")
                        self.logger.warning(msg.format(
                            attr_t, supported_types, NGSI_TEXT))

                        table[attr] = NGSI_TO_PG[NGSI_TEXT]

                else:
                    pg_t = NGSI_TO_PG[attr_t]

                    # Github issue 24: StructuredValue == object or array
                    is_list = isinstance(e[attr].get('value', None), list)
                    if attr_t == NGSI_STRUCTURED_VALUE and is_list:
                        pg_t = PG_JSON_ARRAY

                    table[attr] = pg_t

        # Create/Update metadata table for this type
        table_name = self._et2tn(entity_type, fiware_service)
        self._update_metadata_table(table_name, original_attrs)
        self.conn.commit()

        # Sort out data table, including schema, hyper-table and any
        # new columns.
        self._prepare_data_table(table_name, table, fiware_service)
        self.conn.commit()

        # Gather attribute values
        col_names = sorted(table.keys())
        entries = []  # raw values in same order as column names
        for e in entities:
            values = self._preprocess_values(e, table, col_names,
                                             fiware_servicepath)
            entries.append(values)

        # Insert entities data
        p1 = table_name
        p2 = ', '.join(['"{}"'.format(c.lower()) for c in col_names])
        p3 = ','.join(['?'] * len(col_names))
        stmt = "insert into {} ({}) values ({})".format(p1, p2, p3)
        self.cursor.executemany(stmt, entries)
        self.conn.commit()

        return self.cursor

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

    def _attr_is_structured(self, a):
        if a['value'] is not None and isinstance(a['value'], dict):
            self.logger.info("attribute {} has 'value' attribute of type dict"
                             .format(a))
            return True
        return False

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
                    elif mapped_type == NGSI_TO_PG[NGSI_GEOJSON]:
                        mapped_value = geocoding.geojson.wktcodec.encode_as_wkt(
                            ngsi_value)
                    elif mapped_type == NGSI_TO_PG[NGSI_STRUCTURED_VALUE]:
                        mapped_value = pg8000.PGJsonb(ngsi_value)
                    elif mapped_type == NGSI_TO_PG[NGSI_TEXT]:
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
               "(table_name text primary key, entity_attrs jsonb)"
        op = stmt.format(METADATA_TABLE_NAME)
        self.cursor.execute(op)

        # if self.cursor.rowcount:  # NOTE. rowcount always -1; not supported
            # Table just created!
        #    persisted_metadata = {}
        # else:
        # Bring translation table!
        stmt = "select entity_attrs from {} where table_name = ?"
        self.cursor.execute(stmt.format(METADATA_TABLE_NAME), [table_name])

        # By design, one entry per table_name
        res = self.cursor.fetchall()
        persisted_metadata = res[0][0] if res else {}

        if metadata.keys() - persisted_metadata.keys():
            persisted_metadata.update(metadata)
            stmt = "insert into {} (table_name, entity_attrs) values (?, ?) " \
                   "on conflict (table_name) " \
                   "do update set entity_attrs = ?"
            stmt = stmt.format(METADATA_TABLE_NAME)
            entity_attrs_value = pg8000.PGJsonb(persisted_metadata)
            self.cursor.execute(stmt, (table_name, entity_attrs_value,
                                       entity_attrs_value))
    # TODO: concurrency.
    # This implementation, just like the one in the Crate translator, paves
    # the way to lost updates...


@contextmanager
def postgres_translator_instance():
    conn_data = PostgresConnectionData()
    conn_data.read_env()
    with PostgresTranslator(conn_data) as trans:
        yield trans
