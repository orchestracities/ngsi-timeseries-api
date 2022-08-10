from datetime import datetime
from geocoding.slf.geotypes import *
from exceptions.exceptions import AmbiguousNGSIIdError, UnsupportedOption, \
    NGSIUsageError, InvalidParameterValue, InvalidHeaderValue
from translators import base_translator
from translators.config import SQLTranslatorConfig
from utils.common import iter_entity_attrs
from utils.jsondict import safe_get_value
from utils.maybe import maybe_map
import logging
from geocoding.slf import SlfQuery
import dateutil.parser
from typing import Any, List, Optional, Sequence
from uuid import uuid4

from cache.factory import get_cache, is_cache_available
from translators.insert_splitter import to_insert_batches
from utils.connection_manager import Borg
# NGSI TYPES
# Based on Orion output because official docs don't say much about these :(
NGSI_DATETIME = 'DateTime'
NGSI_ID = 'id'
NGSI_GEOJSON = 'geo:json'
NGSI_LD_GEOMETRY = 'GeoProperty'
NGSI_GEOPOINT = 'geo:point'
NGSI_ISO8601 = 'ISO8601'
NGSI_STRUCTURED_VALUE = 'StructuredValue'
NGSI_TEXT = 'Text'
NGSI_TYPE = 'type'

# QUANTUMLEAP Internals
# A table to store the configuration and metadata of each entity type.
METADATA_TABLE_NAME = "md_ets_metadata"
FIWARE_SERVICEPATH = 'fiware_servicepath'
TENANT_PREFIX = 'mt'
TYPE_PREFIX = 'et'
TIME_INDEX = 'timeindex'
VALID_AGGR_METHODS = ['count', 'sum', 'avg', 'min', 'max']
VALID_AGGR_PERIODS = ['year', 'month', 'day', 'hour', 'minute', 'second']
# The name of the column where we store the original JSON entity received
# in the notification when its corresponding DB row can't be inserted.
ORIGINAL_ENTITY_COL = '__original_ngsi_entity__'
# The name of the entity ID and type columns.
ENTITY_ID_COL = 'entity_id'
ENTITY_TYPE_COL = 'entity_type'

# Default Translation
NGSI_TO_SQL = {
    "Array": 'array',
    "Boolean": 'boolean',
    NGSI_ISO8601: 'timestamp WITH TIME ZONE',
    NGSI_DATETIME: 'timestamp WITH TIME ZONE',
    "Integer": 'bigint',
    # NOT all databases supports geometry
    NGSI_GEOJSON: 'text',
    NGSI_LD_GEOMETRY: 'text',
    SlfPoint.ngsi_type(): 'text',
    SlfLine.ngsi_type(): 'text',
    SlfPolygon.ngsi_type(): 'text',
    SlfBox.ngsi_type(): 'text',
    "Number": 'float',
    NGSI_TEXT: 'text',
    # NOT all databases supports JSON objects
    NGSI_STRUCTURED_VALUE: 'text',
    TIME_INDEX: 'timestamp WITH TIME ZONE NOT NULL'
}


def current_timex() -> str:
    """
    :return: QuantumLeap time index value for the current point in time.
    """
    return datetime.utcnow().isoformat(timespec='milliseconds')


def entity_id(entity: dict) -> Optional[str]:
    """
    Safely get the NGSI ID of the given entity.
    The ID, if present, is expected to be a string, so we convert it if it
    isn't.

    :param entity: the entity.
    :return: the ID string if there's an ID, `None` otherwise.
    """
    return maybe_map(str, safe_get_value(entity, NGSI_ID))


def entity_type(entity: dict) -> Optional[str]:
    """
    Safely get the NGSI type of the given entity.
    The type, if present, is expected to be a string, so we convert it if it
    isn't.

    :param entity: the entity.
    :return: the type string if there's an type, `None` otherwise.
    """
    return maybe_map(str, safe_get_value(entity, NGSI_TYPE))


# TODO: Refactor
# I suggest we refactor both this and the Crate translator using something
# like SQLAlchemy if we want to keep the same approach of doing everything
# in Python, but this isn't exactly a good thing for performance---way too
# many calls on each insert! Perhaps we should come up with a more efficient
# design or at least consider stored procs.

# Recent changes reduced number of queries via caching.
# Regarding SQLAlchemy, investigations showed it does not support
# geographic types for Crate.

class SQLTranslator(base_translator.BaseTranslator):
    NGSI_TO_SQL = NGSI_TO_SQL
    config = SQLTranslatorConfig()

    start_time = None

    def __init__(self, host, port, db_name):
        super(SQLTranslator, self).__init__(host, port, db_name)
        qcm = QueryCacheManager()
        self.cache = qcm.get_query_cache()
        self.default_ttl = None
        if self.cache:
            self.default_ttl = self.cache.default_ttl
        self.start_time = datetime.now()
        self.dbCacheName = 'sql'

    def dispose(self):
        dt = datetime.now() - self.start_time
        time_difference = (dt.days * 24 * 60 * 60 + dt.seconds) \
            * 1000 + dt.microseconds / 1000.0
        self.logger.debug("Translation completed | time={} msec".format(
            str(time_difference)))

    def get_db_cache_name(self):
        return self.dbCacheName

    def sql_error_handler(self, exception):
        raise NotImplementedError

    # TODO is this still needed?
    def _refresh(self, entity_types, fiware_service=None):
        """
        Used for testing purposes only!
        Refreshing ensures a query after an insert retrieves the inserted data.
        :param entity_types: list(str) list of entity types whose tables will
         be refreshed
        """
        table_names = [self._et2tn(et, fiware_service) for et in entity_types]
        table_names.append(METADATA_TABLE_NAME)
        self.cursor.execute("refresh table {}".format(','.join(table_names)))

    def _create_data_table(self, table_name, table, fiware_service):
        raise NotImplementedError

    def _update_data_table(self, table_name, new_columns, fiware_service):
        raise NotImplementedError

    def _create_metadata_table(self):
        raise NotImplementedError

    @staticmethod
    def _get_isoformat(db_timestamp: Any) -> str:
        """
        Converts a DB timestamp value to the equivalent date-time string
        in ISO 8601 format.

        :param db_timestamp: the value of a DB timestamp field. We assume
            all date-time values get stored with the same type by the
            insert procedure.
        :return: the ISO 8601 string.
        """
        raise NotImplementedError

    @staticmethod
    def _et2tn(entity_type, fiware_service=None):
        """
        Return table name based on entity type.
        When specified, fiware_service will define the table schema.
        To avoid conflict with reserved words,
        both schema and table name are prefixed.
        """
        et = '"{}{}"'.format(TYPE_PREFIX, entity_type.lower())
        if fiware_service:
            return '"{}{}".{}'.format(TENANT_PREFIX, fiware_service.lower(),
                                      et)
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

    def insert(self, entities, fiware_service=None, fiware_servicepath='/'):
        if not isinstance(entities, list):
            msg = "Entities expected to be of type list, but got {}"
            raise TypeError(msg.format(type(entities)))

        service_paths = []
        if fiware_servicepath:
            clean_fiware_servicepath = fiware_servicepath.replace(" ", "")
            service_paths = clean_fiware_servicepath.split(",")
        else:
            service_paths = [fiware_servicepath]
        if len(service_paths) == 1:
            entities_by_type = {}
            for e in entities:
                entities_by_type.setdefault(entity_type(e), []).append(e)

            res = None
            for et in entities_by_type.keys():
                res = self._insert_entities_of_type(et,
                                                    entities_by_type[et],
                                                    fiware_service,
                                                    service_paths[0])
        elif len(service_paths) == len(entities):
            entities_by_service_path = {}
            for idx, path in enumerate(service_paths):
                entities_by_service_path.setdefault(path, []).append(
                    entities[idx])
            res = None
            for path in entities_by_service_path.keys():
                entities_by_type = {}
                for e in entities_by_service_path[path]:
                    entities_by_type.setdefault(entity_type(e), []).append(e)

                res = None
                for et in entities_by_type.keys():
                    res = self._insert_entities_of_type(et,
                                                        entities_by_type[et],
                                                        fiware_service,
                                                        path)
        else:
            msg = 'Multiple servicePath are allowed only ' \
                  'if their number match the number of entities'
            raise InvalidHeaderValue('Fiware-ServicePath',
                                     fiware_servicepath, msg)

        return res

    def _insert_entities_of_type(self,
                                 entityType,
                                 entities,
                                 fiware_service=None,
                                 fiware_servicepath='/'):
        # All entities must be of the same type and have a time index
        # Also, an entity can't have an attribute with the same name
        # as that specified by ORIGINAL_ENTITY_COL_NAME.
        for e in entities:
            if entity_type(e) != entityType:
                msg = "Entity {} is not of type {}."
                raise ValueError(msg.format(entity_id(e), entity_type))

            if self.TIME_INDEX_NAME not in e:
                msg = "Translating entity without TIME_INDEX. " \
                      "It should have been inserted by the 'Reporter'. {}"
                logging.warning(msg.format(e))
                e[self.TIME_INDEX_NAME] = current_timex()

            if ORIGINAL_ENTITY_COL in e:
                raise ValueError(
                    f"Entity {entity_id(e)} has a reserved attribute name: " +
                    "'{ORIGINAL_ENTITY_COL_NAME}'")

        # Define column types
        # {column_name -> crate_column_type}
        table = {
            ENTITY_ID_COL: self.NGSI_TO_SQL['Text'],
            ENTITY_TYPE_COL: self.NGSI_TO_SQL['Text'],
            self.TIME_INDEX_NAME: self.NGSI_TO_SQL[TIME_INDEX],
            FIWARE_SERVICEPATH: self.NGSI_TO_SQL['Text'],
            ORIGINAL_ENTITY_COL: self.NGSI_TO_SQL[NGSI_STRUCTURED_VALUE],
            'instanceId': self.NGSI_TO_SQL['Text']
        }

        # Preserve original attr names and types
        # {column_name -> (attr_name, attr_type)}
        original_attrs = {
            ENTITY_TYPE_COL: (NGSI_TYPE, NGSI_TEXT),
            ENTITY_ID_COL: (NGSI_ID, NGSI_TEXT),
            self.TIME_INDEX_NAME: (self.TIME_INDEX_NAME, NGSI_DATETIME),
        }

        for e in entities:
            entityId = entity_id(e)
            for attr in iter_entity_attrs(e):
                if attr == self.TIME_INDEX_NAME:
                    continue

                if isinstance(e[attr], dict) and 'type' in e[attr] \
                        and e[attr]['type'] != 'Property':
                    attr_t = e[attr]['type']
                elif isinstance(e[attr], dict) and 'type' in e[attr] \
                        and e[attr]['type'] == 'Property' \
                        and 'value' in e[attr] \
                        and isinstance(e[attr]['value'], dict) \
                        and '@type' in e[attr]['value'] \
                        and e[attr]['value']['@type'] == 'DateTime':
                    attr_t = NGSI_DATETIME
                elif isinstance(e[attr], dict) and 'value' in e[attr]:
                    value = e[attr]['value']
                    if isinstance(value, list):
                        attr_t = "Array"
                    elif value is not None and isinstance(value, dict):
                        attr_t = NGSI_STRUCTURED_VALUE
                    elif isinstance(value, bool):
                        attr_t = 'Boolean'
                    elif isinstance(value, int):
                        attr_t = 'Integer'
                    elif isinstance(value, float):
                        attr_t = 'Number'
                    elif self._is_iso_date(value):
                        attr_t = NGSI_DATETIME
                    else:
                        attr_t = NGSI_TEXT
                else:
                    attr_t = None

                col = self._ea2cn(attr)
                original_attrs[col] = (attr, attr_t)

                table[col] = self._compute_type(entityId, attr_t, e[attr])

        # Create/Update metadata table for this type
        table_name = self._et2tn(entityType, fiware_service)
        modified = self._update_metadata_table(table_name, original_attrs)
        # Sort out data table.
        if modified and modified == original_attrs.keys():
            self._create_data_table(table_name, table, fiware_service)
        elif modified:
            new_columns = {}
            for k in modified:
                new_columns[k] = table[k]
            self._update_data_table(table_name, new_columns, fiware_service)

        # Gather attribute values
        col_names = sorted(table.keys())
        entries = []  # raw values in same order as column names
        for e in entities:
            values = self._preprocess_values(e, original_attrs, col_names,
                                             fiware_servicepath)
            entries.append(values)

        # Insert entities data
        self._insert_entity_rows(table_name, col_names, entries, entities)
        return self.cursor

    def _insert_entity_rows(self, table_name: str, col_names: List[str],
                            rows: List[List], entities: List[dict]):
        col_list, placeholders, rows = \
            self._build_insert_params_and_values(col_names, rows, entities)

        stmt = f"insert into {table_name} ({col_list}) values ({placeholders})"
        try:
            start_time = datetime.now()

            for batch in to_insert_batches(rows):
                res = self.cursor.executemany(stmt, batch)
                # new version of crate does not bomb anymore when
                # something goes wrong in multi entries
                # simply it returns -2 for each row that have an issue
                # TODO: improve error handling.
                # using batches, we don't need to fail the whole set
                # but only failing batches.
                if isinstance(res, list):
                    for i in range(len(res)):
                        if res[i]['rowcount'] < 0:
                            raise Exception('An insert failed')

            dt = datetime.now() - start_time
            time_difference = (dt.days * 24 * 60 * 60 + dt.seconds) \
                * 1000 + dt.microseconds / 1000.0
            self.logger.debug("Query completed | time={} msec".format(
                str(time_difference)))
        except Exception as e:
            self.sql_error_handler(e)
            if not self._should_insert_original_entities(e):
                raise

            self.logger.exception(
                'Failed to insert entities because of below error; ' +
                'translator will still try saving original JSON in ' +
                f"{table_name}.{ORIGINAL_ENTITY_COL}"
            )
            self._insert_original_entities_in_failed_batch(
                table_name, entities, e)

    def _build_insert_params_and_values(
            self, col_names: List[str], rows: List[List],
            entities: List[dict]) -> (str, str, List[List]):
        if self.config.keep_raw_entity():
            original_entity_col_index = col_names.index(ORIGINAL_ENTITY_COL)
            for i, r in enumerate(rows):
                wrapper = self._build_original_data_value(entities[i])
                r[original_entity_col_index] = wrapper

        col_list = ', '.join(['"{}"'.format(c.lower()) for c in col_names])
        placeholders = ','.join(['?'] * len(col_names))
        return col_list, placeholders, rows

    # NOTE. Brittle code.
    # This code, like the rest of the insert workflow implicitly assumes
    # 1. col_names[k] <-> rows[k] <-> entities[k]
    # 2. original entity column always gets added upfront
    # But we never really check anywhere (1) and (2) always hold true,
    # so slight changes to the insert workflow could cause nasty bugs...

    def _build_original_data_value(self, entity: dict,
                                   insert_error: Exception = None,
                                   failed_batch_id: str = None) -> Any:
        value = {
            'data': entity
        }
        if failed_batch_id:
            value['failedBatchID'] = failed_batch_id
        if insert_error:
            value['error'] = repr(insert_error)

        return self._to_db_ngsi_structured_value(value)

    @staticmethod
    def _to_db_ngsi_structured_value(data: dict) -> Any:
        return data

    def _should_insert_original_entities(self,
                                         insert_error: Exception) -> bool:
        raise NotImplementedError

    def _insert_original_entities_in_failed_batch(
            self, table_name: str, entities: List[dict],
            insert_error: Exception):
        cols = f"{ENTITY_ID_COL}, {ENTITY_TYPE_COL}, {self.TIME_INDEX_NAME}" \
            + f", {ORIGINAL_ENTITY_COL}"
        stmt = f"insert into {table_name} ({cols}) values (?, ?, ?, ?)"
        tix = current_timex()
        batch_id = uuid4().hex
        rows = [[entity_id(e), entity_type(e), tix,
                 self._build_original_data_value(e, insert_error, batch_id)]
                for e in entities]

        self.cursor.executemany(stmt, rows)

    def _attr_is_structured(self, a):
        if 'value' in a and a['value'] is not None \
                and isinstance(a['value'], dict):
            self.logger.debug("attribute {} has 'value' attribute of type dict"
                              .format(a))
            return True
        return False

    @staticmethod
    def is_text(attr_type):
        return attr_type == NGSI_TEXT or attr_type not in NGSI_TO_SQL

    def _preprocess_values(self, e, original_attrs, col_names,
                           fiware_servicepath):
        values = []
        for cn in col_names:
            if cn == ENTITY_TYPE_COL:
                values.append(entity_type(e))
            elif cn == ENTITY_ID_COL:
                values.append(entity_id(e))
            elif cn == self.TIME_INDEX_NAME:
                values.append(e[self.TIME_INDEX_NAME])
            elif cn == FIWARE_SERVICEPATH:
                values.append(fiware_servicepath or '/')
            elif cn == 'instanceId':
                values.append("urn:ngsi-ld:" + str(uuid4()))
            else:
                # Normal attributes
                try:
                    attr = original_attrs[cn][0]
                    attr_t = original_attrs[cn][1]

                    if SlfGeometry.is_ngsi_slf_attr(e[attr]):
                        mapped_value = self._ngsi_slf_to_db(e[attr])
                    elif attr_t == NGSI_GEOJSON or attr_t == NGSI_LD_GEOMETRY:
                        mapped_value = self._ngsi_geojson_to_db(e[attr])
                    elif self._is_ngsi_ld_datetime_property(e[attr]):
                        mapped_value = self._ngsi_ld_datetime_to_db(e[attr])
                    elif attr_t == NGSI_TEXT:
                        mapped_value = self._ngsi_text_to_db(e[attr])
                    elif attr_t == NGSI_DATETIME or attr_t == NGSI_ISO8601:
                        mapped_value = self._ngsi_datetime_to_db(e[attr])
                    elif attr_t == "Boolean":
                        mapped_value = self._ngsi_boolean_to_db(e[attr])
                    elif attr_t == "Number":
                        mapped_value = self._ngsi_number_to_db(e[attr])
                    elif attr_t == "Integer":
                        mapped_value = self._ngsi_integer_to_db(e[attr])
                    elif attr_t == 'Relationship':
                        mapped_value = self._ngsi_ld_relationship_to_db(
                            e[attr])
                    elif self._is_ngsi_array(e[attr], attr_t):
                        mapped_value = self._ngsi_array_to_db(e[attr])
                    elif self._is_ngsi_object(e[attr], attr_t):
                        mapped_value = self._ngsi_structured_to_db(e[attr])
                    else:
                        mapped_value = self._ngsi_default_to_db(e[attr])

                    values.append(mapped_value)
                except KeyError:
                    # this entity update does not have a value for the column
                    # so use None which will be inserted as NULL to the db.
                    values.append(None)
                except ValueError:
                    # this value cannot be cast to column type
                    # so use None which will be inserted as NULL to the db.
                    values.append(None)
        return values

    @staticmethod
    def _is_ngsi_array(attr, attr_t):
        return (attr_t == NGSI_STRUCTURED_VALUE and 'value' in attr
                and isinstance(attr['value'], list)) \
            or ('value' in attr and isinstance(attr['value'], list)) \
            or attr_t == "Array"

    @staticmethod
    def _is_ngsi_object(attr, attr_t):
        return attr_t == NGSI_STRUCTURED_VALUE or (
            'value' in attr and isinstance(attr['value'], dict))

    @staticmethod
    def _is_ngsi_ld_datetime_property(attr):
        if 'type' in attr and attr[
                'type'] == 'Property' and 'value' in attr and isinstance(
                attr['value'], dict) \
            and '@type' in attr['value'] and attr['value'][
                '@type'] == 'DateTime':
            return True
        return False

    @staticmethod
    def _ngsi_geojson_to_db(attr):
        raise NotImplementedError

    @staticmethod
    def _ngsi_number_to_db(attr):
        try:
            if isinstance(attr['value'], bool):
                return None
            elif isinstance(attr['value'], float):
                return attr['value']
            elif attr['value'] is not None:
                return float(attr['value'])
        except (ValueError, TypeError) as e:
            logging.warning(
                '{} cannot be cast to {} replaced with None'.format(
                    attr.get('value', None), attr.get('type', None)))
            return None
        else:
            logging.warning(
                '{} cannot be cast to {} replaced with None'.format(
                    attr.get('value', None), attr.get('type', None)))
            return None

    @staticmethod
    def _ngsi_datetime_to_db(attr):
        if 'value' in attr and SQLTranslator._is_iso_date(attr['value']):
            return attr['value']
        else:
            logging.warning(
                '{} cannot be cast to {} replaced with None'.format(
                    attr.get('value', None), attr.get('type', None)))
            return None

    @staticmethod
    def _ngsi_integer_to_db(attr):
        try:
            if isinstance(attr['value'], bool):
                return None
            elif isinstance(attr['value'], int):
                return attr['value']
            elif attr['value'] is not None:
                return int(float(attr['value']))
        except (ValueError, TypeError) as e:
            logging.warning(
                '{} cannot be cast to {} replaced with None'.format(
                    attr.get('value', None), attr.get('type', None)))
            return None
        else:
            logging.warning(
                '{} cannot be cast to {} replaced with None'.format(
                    attr.get('value', None), attr.get('type', None)))
            return None

    @staticmethod
    def _ngsi_boolean_to_db(attr):
        if isinstance(attr['value'], str) and attr['value'].lower() == 'true':
            return True
        elif isinstance(attr['value'], str) \
                and attr['value'].lower() == 'false':
            return False
        elif isinstance(attr['value'], int) and attr['value'] == 1:
            return True
        elif isinstance(attr['value'], int) and attr['value'] == 0:
            return False
        elif isinstance(attr['value'], bool):
            return attr['value']
        else:
            logging.warning(
                '{} cannot be cast to {} replaced with None'.format(
                    attr.get('value', None), attr.get('type', None)))
            return None

    @staticmethod
    def _ngsi_slf_to_db(attr):
        raise NotImplementedError

    @staticmethod
    def _ngsi_structured_to_db(attr):
        raise NotImplementedError

    @staticmethod
    def _ngsi_array_to_db(attr):
        raise NotImplementedError

    @staticmethod
    def _ngsi_text_to_db(attr):
        if 'value' in attr and attr['value'] is not None:
            return str(attr['value'])
        logging.warning('{} cannot be cast to {} replaced with None'.format(
            attr.get('value', None), attr.get('type', None)))
        return None

    @staticmethod
    def _ngsi_default_to_db(attr):
        return attr.get('value', None)

    @staticmethod
    def _ngsi_ld_datetime_to_db(attr):
        if SQLTranslator._is_ngsi_ld_datetime_property(
                attr) and SQLTranslator._is_iso_date(attr['value']['@value']):
            return attr['value']['@value']
        else:
            if 'value' in attr:
                logging.warning(
                    '{} cannot be cast to {} replaced with None'.format(
                        attr['value'],
                        'datetime'))
            else:
                logging.warning(
                    'attribute "value" is missing, cannot perform cast')
            return None

    @staticmethod
    def _ngsi_ld_relationship_to_db(attr):
        return attr.get('value', None) or attr.get('object', None)

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

        if not self._is_query_in_cache(self.dbCacheName, METADATA_TABLE_NAME):
            self._create_metadata_table()
            self._cache(self.dbCacheName,
                        METADATA_TABLE_NAME,
                        "",
                        self.default_ttl)

        # Bring translation table!
        stmt = "select entity_attrs from {} where table_name = ?".format(
            METADATA_TABLE_NAME)

        # By design, one entry per table_name
        try:
            res = self._execute_query_via_cache(self.dbCacheName,
                                                table_name,
                                                stmt,
                                                [table_name],
                                                self.default_ttl)
            persisted_metadata = res[0][0] if res else {}
        except Exception as e:
            self.sql_error_handler(e)
            # Metadata table still not created
            logging.debug(str(e), exc_info=True)
            # Attempt to re-create metadata table
            self._create_metadata_table()
            persisted_metadata = {}

        diff = metadata.keys() - persisted_metadata.keys()
        if diff:
            # we update using the difference to "not" corrupt the metadata
            # by previous insert
            update = dict((k, metadata[k]) for k in diff if k in metadata)
            persisted_metadata.update(update)
            self._store_metadata(table_name, persisted_metadata)
            self._cache(self.dbCacheName,
                        table_name,
                        [[persisted_metadata]],
                        self.default_ttl)
        return diff
        # TODO: concurrency.
        # This implementation paves
        # the way to lost updates...

    def _store_metadata(self, table_name, persisted_metadata):
        raise NotImplementedError

    def _get_et_table_names(self, fiware_service=None):
        """
        Return the names of all the tables representing entity types.
        :return: list(unicode)
        """
        stmt = "select distinct table_name from {}".format(METADATA_TABLE_NAME)
        key = ""
        if fiware_service:
            key = fiware_service.lower()
            where = " where table_name ~* '\"{}{}\"[.].*'"
            stmt += where.format(TENANT_PREFIX, key)
        else:
            where = " where table_name !~* '\"{}{}\"[.].*'"
            stmt += where.format(TENANT_PREFIX, '.*')
        try:
            table_names = self._execute_query_via_cache(key,
                                                        "tableNames",
                                                        stmt,
                                                        [],
                                                        self.default_ttl)
        except Exception as e:
            self.sql_error_handler(e)
            self.logger.error(str(e), exc_info=True)
            return []
        return [r[0] for r in table_names]

    def _get_select_clause(
            self,
            attr_names,
            aggr_method,
            aggr_period,
            prefix=''):
        if not attr_names:
            return prefix + '*'

        attrs = [prefix + ENTITY_TYPE_COL, prefix + ENTITY_ID_COL]
        if aggr_method:
            if aggr_period:
                attrs.append(
                    "DATE_TRUNC('{}',{}) as {}".format(
                        aggr_period, self.TIME_INDEX_NAME,
                        self.TIME_INDEX_NAME)
                )
            # TODO:
            # https://github.com/orchestracities/ngsi-timeseries-api/issues/106
            m = '{}("{}") as "{}"'
            attrs.extend(m.format(aggr_method, a, a) for a in set(attr_names))

        else:
            attrs.append(prefix + self.TIME_INDEX_NAME)
            attrs.extend(prefix + '"{}"'.format(a) for a in attr_names)

        select = ','.join(attrs)
        return select

    def _get_limit(self, limit, last_n):
        # https://crate.io/docs/crate/reference/en/latest/general/dql/selects.html#limits
        default_limit = self.config.default_limit()

        if limit is None or limit > default_limit:
            limit = default_limit

        if last_n is None:
            last_n = limit

        if limit < 1:
            raise InvalidParameterValue(
                f"limit should be >=1 and <= {default_limit}.")
        if last_n < 1:
            raise InvalidParameterValue(
                f"last_n should be >=1 and <= {default_limit}.")
        return min(last_n, limit)

    def _get_where_clause(
            self,
            entity_ids,
            from_date,
            to_date,
            idPattern,
            fiware_sp='/',
            geo_query=None,
            prefix=''):
        clauses = []
        where_clause = ""

        if entity_ids:
            ids = ",".join("'{}'".format(e) for e in entity_ids)
            clauses.append(" {}entity_id in ({}) ".format(prefix, ids))
        if from_date:
            clauses.append(" {}{} >= '{}'".format(prefix, self.TIME_INDEX_NAME,
                                                  self._parse_date(from_date)))
        if to_date:
            clauses.append(" {}{} <= '{}'".format(prefix, self.TIME_INDEX_NAME,
                                                  self._parse_date(to_date)))

        if fiware_sp:
            # Match prefix of fiware service path
            if fiware_sp == '/':
                clauses.append(
                    " " + prefix + FIWARE_SERVICEPATH + " ~* '/.*'")
            else:
                clauses.append(
                    " " + prefix + FIWARE_SERVICEPATH + " ~* '"
                    + fiware_sp + "($|/.*)'")
        else:
            # Match prefix of fiware service path
            clauses.append(" " + prefix + FIWARE_SERVICEPATH + " = ''")

        if idPattern:
            clauses.append(
                " " +
                prefix +
                ENTITY_ID_COL +
                " ~* '" +
                idPattern +
                "($|.*)'")

        # TODO implement prefix also for geo_clause
        geo_clause = self._get_geo_clause(geo_query)
        if geo_clause:
            clauses.append(geo_clause)

        if len(clauses) > 0:
            where_clause = "where" + " and ".join(clauses)
        return where_clause

    @staticmethod
    def _parse_date(date):
        try:
            return dateutil.parser.isoparse(date.strip('\"')).isoformat()
        except Exception as e:
            raise InvalidParameterValue(date, "**fromDate** or **toDate**")

    @staticmethod
    def _is_iso_date(date):
        try:
            dateutil.parser.isoparse(date.strip('\"')).isoformat()
            return True
        except Exception as e:
            return False

    @staticmethod
    def _parse_limit(limit):
        if (not (limit is None or isinstance(limit, int))):
            raise InvalidParameterValue(limit, "limit")
        return limit

    @staticmethod
    def _parse_last_n(last_n):
        if (not (last_n is None or isinstance(last_n, int))):
            raise InvalidParameterValue(last_n, "last_n")
        return last_n

    def _get_geo_clause(self, geo_query: SlfQuery = None) -> Optional[str]:
        raise NotImplementedError

    def _get_order_group_clause(self, aggr_method, aggr_period,
                                select_clause, last_n):
        order_by = []
        group_by = []

        # Group By
        if aggr_method and select_clause != "*":
            group_by.extend(["entity_type", "entity_id"])
            if aggr_period:
                # Note: If alias shadows a real table column,
                # grouping will NOT be applied on the aliased column
                gb = "DATE_TRUNC('{}', {})".format(
                    aggr_period, self.TIME_INDEX_NAME)
                group_by.append(gb)

        # Order by
        direction = "DESC" if last_n else "ASC"

        if aggr_method:
            if aggr_period:
                # consider always ordering by entity_id also
                order_by.extend(["entity_type", "entity_id"])
                order_by.append(
                    "{} {}".format(self.TIME_INDEX_NAME, direction))
        else:
            order_by.append("{} {}".format(self.TIME_INDEX_NAME, direction))

        clause = ""
        if group_by:
            clause = "GROUP BY {}".format(",".join(group_by))
        if order_by:
            clause += " ORDER BY {}".format(",".join(order_by))
        return clause

    def query(self,
              attr_names=None,
              entity_type=None,
              entity_id=None,
              entity_ids=None,
              where_clause=None,
              aggr_method=None,
              aggr_period=None,
              aggr_scope=None,
              from_date=None,
              to_date=None,
              last_n=None,
              limit=10000,
              offset=0,
              idPattern=None,
              fiware_service=None,
              fiware_servicepath='/',
              geo_query: SlfQuery = None):
        """
        This translator method is used by all API query endpoints.

        :param attr_names:
            Array of attribute names to query for.
        :param entity_type:
            (Optional). NGSI Entity Type to query about. Unique and optional
            as long as there are no 2 equal NGSI ids for any NGSI type.
        :param entity_id:
            NGSI Id of the entity you ask for. Cannot be used with entity_ids.
        :param entity_ids:
            Array of NGSI ids to consider in the response. Cannot be used with
            entity_id.
        :param where_clause:
            (Optional), to use a custom SQL query (not open to public API).
        :param aggr_method:
            (Optional), function to apply to the queried values. Must be one
            of the VALID_AGGR_METHODS (e.g, sum, avg, etc). You need to specify
            at least one attribute in attr_names, otherwise this will be
            ignored.
        :param aggr_period:
            (Optional), only valid when using aggr_method. Defines the time
            scope on to which the aggr_method will be applied, hence defines
            also the number of values that will be returned. Must be one of the
            VALID_AGGR_PERIODS (e.g, hour). I.e., querying avg per hour will
            return 24 values times the number of days of available measurements
        :param aggr_scope: (Not Implemented). Defaults to "entity", which means
            the aggrMethod will be applied N times, once for each entityId.
            "global" instead would allow cross-entity_id aggregations.
        :param from_date:
            (Optional), used to filter results, considering only from this date
            inclusive.
        :param to_date:
            (Optional), used to filter results,
            considering only up to this date inclusive.
        :param last_n:
            (Optional), used to filter results, return only the last_n elements
            of what would be the result of the query once all filters where
            applied.
        :param limit:
            (Optional), used to filter results, return up to limit elements
            of what would be the result of the query once all filters where
            applied.
        :param offset:
            (Optional), used to page results.
        :param fiware_service:
            (Optional), used to filter results, considering in the result only
            entities in this FIWARE Service.
        :param fiware_servicepath:
            (Optional), used to filter results, considering in the result only
            entities in this FIWARE ServicePath.
        :param geo_query:
            (Optional), filters results with an NGSI geo query.

        :return:
        The shape of the response is always something like this:

        [{
         'type': 'Room',
         'id': 'Room1', or 'ids': ['Room1', 'Room2'],
         'index': [t0, t1, ..., tn],
         'attr_1': {
             'index': [t0, t1, ..., tn], # index of this attr (if different)
             'values': [v0, v1, ..., vn],
             'type': Number
         },
         ...,
         'attr_N': ...
        },...
        ]

        It returns an array of dictionaries, each representing a query result
        on a particular NGSI Entity Type. Each of the dicts in this array
        consists of the following attributes.

        'type' is the NGSI Entity Type of the response.

        'id' or 'ids'. id if the response contains data from a specific NGSI
        entity (with that id) or ids in the case the response aggregates data
        from multiple entities (those with those ids). You get one or the
        other, not both.

        'index': The time index applying to the response, applies to all
        attributes included in the response. It may not be present if each
        attribute has its own time index array, in the cases where attributes
        are measured at different moments in time. Note since this is a
        "global" time index for the entity, it may contain some NULL values
        where measurements were not available. It's an array containing time
        in ISO format representation, typically in the original timezone the
        Orion Notification used, or UTC if created within QL.

        Each attribute in the response will be represented by a dictionary,
        with an array called 'values' containing the actual historical values
        of the attributes as queried. An attribute 'type' will have the
        original NGSI type of the attribute (i.e, the type of each of the
        elements now in the values array). The type of an attribute is not
        expected to change in time, that'd be an error. Additionally, it may
        contain an array called 'index', just like the global index
        discussed above but for this specific attribute. Thus, this 'index'
        will never contain NONE values.

        If the user did not specify an aggrMethod, the response will not mix
        measurements of different entities in the same values array. So in this
        case, there will be many dictionaries in the response array, one for
        each NGSI Entity.

        When using aggrPeriod, the index array is a completely new index,
        composed of time steps of the original index of the attribute but
        zeroing the less significant bits of time. For example, if there were
        measurements in time 2018-04-03T08:15:15 and 2018-04-03T09:01:15, with
        aggrPeriod = minute the new index will contain, at least, the steps
        2018-04-03T08:15:00 and 2018-04-03T09:01:00 respectively.

        :raises:
        ValueError in case of misuse of the attributes.
        UnsupportedOption for still-to-be-implemented features.
        crate.DatabaseError in case of errors with CrateDB interaction.
        """
        last_n = self._parse_last_n(last_n)
        limit = self._parse_limit(limit)

        result = []
        message = 'ok'

        if last_n == 0 or limit == 0:
            return (result, message)

        if entity_id and entity_ids:
            raise NGSIUsageError("Cannot use both entity_id and entity_ids "
                                 "params in the same call.")

        if aggr_method and aggr_method.lower() not in VALID_AGGR_METHODS:
            raise UnsupportedOption("aggr_method={}".format(aggr_method))

        if aggr_period and aggr_period.lower() not in VALID_AGGR_PERIODS:
            raise UnsupportedOption("aggr_period={}".format(aggr_period))

        # TODO check also entity_id and entity_type to not be SQL injection
        if entity_id and not entity_type:
            entity_type = self._get_entity_type(entity_id, fiware_service)

            if not entity_type:
                return (result, message)

            if len(entity_type.split(',')) > 1:
                raise AmbiguousNGSIIdError(entity_id)

        if entity_id:
            entity_ids = tuple([entity_id])

        lower_attr_names = [a.lower() for a in attr_names] \
            if attr_names else attr_names
        select_clause = self._get_select_clause(lower_attr_names,
                                                aggr_method,
                                                aggr_period)
        if not where_clause:
            where_clause = self._get_where_clause(entity_ids,
                                                  from_date,
                                                  to_date,
                                                  idPattern,
                                                  fiware_servicepath,
                                                  geo_query)

        order_group_clause = self._get_order_group_clause(aggr_method,
                                                          aggr_period,
                                                          select_clause,
                                                          last_n)

        if entity_type:
            table_names = [self._et2tn(entity_type, fiware_service)]
        else:
            table_names = self._get_et_table_names(fiware_service)

        limit = self._get_limit(limit, last_n)
        offset = max(0, offset)

        for tn in sorted(table_names):
            op = "select {select_clause} " \
                 "from {tn} " \
                 "{where_clause} " \
                 "{order_group_clause} " \
                 "limit {limit} offset {offset}".format(
                     select_clause=select_clause,
                     tn=tn,
                     where_clause=where_clause,
                     order_group_clause=order_group_clause,
                     limit=limit,
                     offset=offset,
                 )
            try:
                self.cursor.execute(op)

            except Exception as e:
                # TODO due to this except in case of sql errors,
                # all goes fine, and users gets 404 as result
                # Reason 1: fiware_service_path column in legacy dbs.
                err_msg = self.sql_error_handler(e)
                self.logger.error(str(e), exc_info=True)
                entities = []
                if err_msg:
                    message = err_msg
            else:
                res = self.cursor.fetchall()
                col_names = self._column_names_from_query_meta(
                    self.cursor.description)
                entities = self._format_response(res,
                                                 col_names,
                                                 tn,
                                                 last_n)
            result.extend(entities)
        return (result, message)

    @staticmethod
    def _column_names_from_query_meta(cursor_description: Sequence) -> [str]:
        """
        List the name of the columns returned by a query.

        :param cursor_description: the value of the cursor's `description`
            attribute after fetching the query results.
        :return: the column names.
        """
        raise NotImplementedError

    def query_ids(self,
                  entity_type=None,
                  from_date=None,
                  to_date=None,
                  limit=10000,
                  offset=0,
                  idPattern=None,
                  fiware_service=None,
                  fiware_servicepath='/'):
        if limit == 0:
            return []

        where_clause = self._get_where_clause(None,
                                              from_date,
                                              to_date,
                                              idPattern,
                                              fiware_servicepath,
                                              None)

        if entity_type:
            table_names = [self._et2tn(entity_type, fiware_service)]
        else:
            table_names = self._get_et_table_names(fiware_service)

        if fiware_service is None:
            for tn in table_names:
                if "." in tn:
                    table_names.remove(tn)
        limit = min(10000, limit)
        offset = max(0, offset)
        len_tn = 0
        result = []
        stmt = ""
        if len(table_names) > 0:
            for tn in sorted(table_names):
                len_tn += 1
                stmt += "select " \
                        "entity_id, " \
                        "entity_type, " \
                        "max(time_index) as time_index " \
                        "from {tn} {where_clause} " \
                        "group by entity_id, entity_type".format(
                            tn=tn,
                            where_clause=where_clause
                        )
                if len_tn != len(table_names):
                    stmt += " union all "

            op = stmt + " ORDER BY time_index DESC, entity_type, entity_id limit {limit} offset {offset}".format(
                offset=offset, limit=limit)

            try:
                self.cursor.execute(op)
            except Exception as e:
                self.sql_error_handler(e)
                self.logger.error(str(e), exc_info=True)
                entities = []
            else:
                res = self.cursor.fetchall()
                col_names = [ENTITY_ID_COL, ENTITY_TYPE_COL, 'time_index']
                entities = self._format_response(res,
                                                 col_names,
                                                 table_names,
                                                 None)
            result.extend(entities)
        return result

    def query_last_value(self,
                         entity_ids=None,
                         entity_type=None,
                         attr_names=None,
                         from_date=None,
                         to_date=None,
                         limit=10000,
                         offset=0,
                         idPattern=None,
                         fiware_service=None,
                         fiware_servicepath='/'):
        if limit == 0:
            return []
        # todo filter only selected attributes.

        lower_attr_names = [a.lower() for a in attr_names] \
            if attr_names else attr_names

        if entity_type:
            table_names = [self._et2tn(entity_type, fiware_service)]
        else:
            table_names = self._get_et_table_names(fiware_service)

        if fiware_service is None:
            for tn in table_names:
                if "." in tn:
                    table_names.remove(tn)
        limit = min(10000, limit)
        offset = max(0, offset)
        len_tn = 0
        result = []
        stmt = ""
        if len(table_names) > 0:
            for tn in sorted(table_names):
                len_tn += 1
                prefix = 'a{len_tn}.'.format(
                    len_tn=len_tn
                )
                select_clause = self._get_select_clause(lower_attr_names, None,
                                                        None, prefix=prefix)
                where_clause_no_prefix = self._get_where_clause(
                    entity_ids, from_date, to_date, idPattern, fiware_servicepath, None)
                where_clause = self._get_where_clause(entity_ids,
                                                      from_date,
                                                      to_date,
                                                      idPattern,
                                                      fiware_servicepath,
                                                      None, prefix=prefix)
                stmt += "select {select} " \
                        "from {tn} as a{len_tn} " \
                        "join (select " \
                        "entity_id, entity_type, " \
                        "max(time_index) as time_index " \
                        "from {tn} {where_clause_no_prefix} " \
                        "group by entity_id, entity_type) b{len_tn} " \
                        "on a{len_tn}.entity_id = b{len_tn}.entity_id " \
                        "and a{len_tn}.entity_type = b{len_tn}.entity_type " \
                        "and a{len_tn}.time_index = b{len_tn}.time_index " \
                        "{where_clause} ".format(
                            select=select_clause,
                            tn=tn,
                            len_tn=len_tn,
                            where_clause_no_prefix=where_clause_no_prefix,
                            where_clause=where_clause
                        )
                if len_tn != len(table_names):
                    stmt += " union all "

            # TODO ORDER BY time_index asc is removed for the time being
            #  till we have a solution for
            #  https://github.com/crate/crate/issues/9854
            op = stmt + "ORDER BY time_index DESC limit {limit} offset {offset}".format(
                offset=offset,
                limit=limit
            )

            try:
                self.cursor.execute(op)
            except Exception as e:
                self.sql_error_handler(e)
                self.logger.error(str(e), exc_info=True)
                entities = []
            else:
                res = self.cursor.fetchall()
                col_names = self._column_names_from_query_meta(
                    self.cursor.description)
                entities = self._format_response(res,
                                                 col_names,
                                                 table_names,
                                                 None,
                                                 True)
            result.extend(entities)
        return result

    def query_instanceId(self,
                         entity_id=None,
                         entity_type=None,
                         from_date=None,
                         to_date=None,
                         limit=10000,
                         offset=0,
                         idPattern=None,
                         fiware_service=None,
                         fiware_servicepath=None):
        if limit == 0:
            return []

        if entity_id and not entity_type:
            entity_type = self._get_entity_type(entity_id, fiware_service)

            if not entity_type:
                return []

            if len(entity_type.split(',')) > 1:
                raise AmbiguousNGSIIdError(entity_id)

        if entity_type:
            table_names = [self._et2tn(entity_type, fiware_service)]
        else:
            table_names = self._get_et_table_names(fiware_service)

        if entity_id:
            entity_ids = tuple([entity_id])

        where_clause = self._get_where_clause(entity_ids,
                                              from_date,
                                              to_date,
                                              idPattern,
                                              fiware_servicepath)

        limit = min(10000, limit)
        offset = max(0, offset)
        result = []
        if len(table_names) > 0:
            for tn in sorted(table_names):
                op = "select instanceId " \
                     "from {tn} " \
                     "{where_clause} " \
                     "limit {limit} offset {offset}".format(
                         tn=tn,
                         where_clause=where_clause,
                         limit=limit,
                         offset=offset
                     )

                try:
                    self.cursor.execute(op)
                except Exception as e:
                    self.sql_error_handler(e)
                    self.logger.error(str(e), exc_info=True)
                    entities = []
                else:
                    res = self.cursor.fetchall()
                    result.extend(res)
        return result

    def _format_response(
            self,
            resultset,
            col_names,
            table_names,
            last_n,
            single_value=False):
        """
        :param resultset: list of query results for one entity_type
        :param col_names: list of columns affected in the query
        :param table_names: names of tables where the query took place.
        :param last_n: see last_n in query method.
        :param aggr_method: True if used in the request, false otherwise.
        :param last_value: True if we return a single value for entity.

        :return: list of dicts. Possible scenarios

        Without aggrMethod, there will be one dict per entity instance. E.g.,
        returns [
                {'type': 'Room',
                'id': 'Room1',
                'temperature': {'values': [1, 2, 3], 'type': 'Number'}
                'index: [t0, t1, t2]
                },
                {'type': 'Room',
                'id': 'Room2',
                'temperature': {'values': [5, 6, 4], 'type': 'Number'}
                'index: [t0, t1, t2]
                }
                ]

        With aggrMethod and one specific id requested, the list has only one
        dict. The number of values is 1 if no aggrPeriod was asked for,
        or one value per aggregation period step.
        returns [{
                    'type': 'Room',
                    'id': 'SpecificRoom',
                    'temperature': {'values': [1, 2, 3], ...}, # aggregated
                    'index': [tA, tB, tC]                      # aggrPeriod
                }]

        With aggrMethod and global aggrScope (NOT YET IMPLEMENTED),
        the array has only one dict, but instead of an 'id' attribute it will
        have an 'ids', with all the ids that were cross-aggregated.
        returns [{
                    'type': 'Room',
                    'ids': ['Room1', 'Room2'],
                    'temperature': {'values': [4,], ...},       # aggregated
                    'index': [],                                # aggrPeriod
                }]

        Indexes elements are time steps in ISO format.
        """
        if isinstance(table_names, str):
            table_names = [table_names]
        cursors = ', '.join(list(map(lambda x: '?', table_names)))
        stmt = "select table_name, entity_attrs from {} " \
               "where table_name in ({})".format(METADATA_TABLE_NAME, cursors)

        try:
            # TODO we tested using cache here, but with current "delete"
            #  approach this causes issues scenario triggering the issue is:
            #  a entity is create, delete is used to delete all values what
            #  happens is that the table is empty, but metadata are still
            #  there, so caching the query with res =
            #  self._execute_query_via_cache(table_name, "metadata", stmt,
            #  [table_name], self.default_ttl) actually create an entry in
            #  the cache table_name, "metadata" in a following query call (
            #  below ttl) the same cache can be called despite there is no
            #  data. a possible solution is to create a cache based on query
            #  parameters that would cache all the results
            self.cursor.execute(stmt, table_names)
            res = self.cursor.fetchall()
        except Exception as e:
            self.sql_error_handler(e)
            self.logger.error(str(e), exc_info=True)
            res = {}

        entities = {}

        if last_n:
            # LastN induces DESC order, but we always return ASC order.
            resultset = reversed(resultset)

        for t in table_names:
            entity_attrs = [tup[1] for tup in res if tup[0] == t]
            if len(entity_attrs) == 0:
                continue
            if len(entity_attrs) > 1:
                msg = "Cannot have {} entries in table '{}' for PK '{}'"
                msg = msg.format(len(res), METADATA_TABLE_NAME, t)
                self.logger.error(msg)
                raise RuntimeError(msg)
            entity_attrs = entity_attrs[0]
            idx_entity_type = col_names.index(ENTITY_TYPE_COL)
            if idx_entity_type < 0:
                msg = "entity_type not available"
                self.logger.error(msg)
                raise RuntimeError(msg)
            entity_type_resultset = [
                item for item in resultset if item[idx_entity_type].lower() in t]
            for r in entity_type_resultset:
                for k, v in zip(col_names, r):
                    if k not in entity_attrs:
                        # implementation-specific columns not representing attrs
                        # e.g. fiware-servicepath
                        continue

                    e_id = r[col_names.index(ENTITY_ID_COL)]
                    e = entities.setdefault(e_id, {})
                    original_name, original_type = entity_attrs[k]

                    if original_name in (NGSI_TYPE, NGSI_ID):
                        e[original_name] = v

                    elif original_name == self.TIME_INDEX_NAME:
                        v = self._get_isoformat(v)
                        if single_value:
                            n = {
                                'value': v,
                                'type': 'DateTime'
                            }
                            e.setdefault('dateModified', n)
                        else:
                            e.setdefault('index', []).append(v)

                    else:
                        attr_dict = e.setdefault(original_name, {})
                        v = self._db_value_to_ngsi(v, original_type)
                        if single_value:
                            attr_dict.setdefault('value', v)
                        else:
                            attr_dict.setdefault('values', []).append(v)
                        attr_dict['type'] = original_type

        return [entities[k] for k in sorted(entities.keys())]

    def _db_value_to_ngsi(self, db_value: Any, ngsi_type: str) -> Any:
        """
        Transform a DB value to its corresponding NGSI value.
        This procedure should be the inverse of the one used to transform NGSI
        entity attribute values to DB values when inserting entities.

        :param db_value: the value to transform.
        :param ngsi_type: the target NGSI type.
        :return: the NGSI value.
        """
        raise NotImplementedError

    def delete_entity(self, eid, etype=None, from_date=None,
                      to_date=None, fiware_service=None,
                      fiware_servicepath='/'):
        if not eid:
            raise NGSIUsageError("entity_id cannot be None nor empty")

        if not etype:
            etype = self._get_entity_type(eid, fiware_service)

            if not etype:
                return 0

            if len(etype.split(',')) > 1:
                raise AmbiguousNGSIIdError(eid)

        return self.delete_entities(etype, eid=[eid],
                                    from_date=from_date, to_date=to_date,
                                    fiware_service=fiware_service,
                                    fiware_servicepath=fiware_servicepath)

    def delete_entities(
            self,
            etype,
            eid=None,
            from_date=None,
            to_date=None,
            idPattern=None,
            fiware_service=None,
            fiware_servicepath='/'):
        table_name = self._et2tn(etype, fiware_service)
        where_clause = self._get_where_clause(eid,
                                              from_date,
                                              to_date,
                                              idPattern,
                                              fiware_servicepath)
        op = "delete from {} {}".format(table_name, where_clause)
        try:
            self.cursor.execute(op)
            key = ""
            if fiware_service:
                key = fiware_service.lower()
            self._remove_from_cache(self.dbCacheName, table_name)
            self._remove_from_cache(key, "tableNames")
            return self.cursor.rowcount
        except Exception as e:
            self.sql_error_handler(e)
            self.logger.error(str(e), exc_info=True)
            return 0

    def drop_table(self, etype, fiware_service=None):
        table_name = self._et2tn(etype, fiware_service)
        op = "drop table {}".format(table_name)
        try:
            self.cursor.execute(op)
        except Exception as e:
            self.sql_error_handler(e)
            self.logger.error(str(e), exc_info=True)

        # Delete entry from metadata table
        op = "delete from {} where table_name = ?".format(METADATA_TABLE_NAME)
        try:
            self.cursor.execute(op, [table_name])
            self._remove_from_cache(self.dbCacheName, table_name)
            key = ""
            if fiware_service:
                key = fiware_service.lower()
            self._remove_from_cache(key, "tableNames")
        except Exception as e:
            self.sql_error_handler(e)
            self.logger.error(str(e), exc_info=True)

        # TODO this can be removed most probably
        if self.cursor.rowcount == 0 and table_name.startswith('"'):
            # See GH #173
            old_tn = ".".join([x.strip('"') for x in table_name.split('.')])
            try:
                self.cursor.execute(op, [old_tn])
            except Exception as e:
                self.sql_error_handler(e)
                self.logger.error(str(e), exc_info=True)

    def query_entity_types(self, fiware_service=None, fiware_servicepath='/'):
        """
        Find the types of for a given fiware_service and fiware_servicepath.
        :return: list of strings.
        """
        # Filter using tenant information
        if fiware_service is None:
            wc = "where table_name NOT like '\"{}%.%'".format(TENANT_PREFIX)
        else:
            # Old is prior QL 0.6.0. GH #173
            old_prefix = '{}{}'.format(TENANT_PREFIX, fiware_service.lower())
            prefix = self._et2tn("FooType", fiware_service).split('.')[0]
            wc = "where table_name like '{}.%' " \
                 "or table_name like '{}.%'".format(old_prefix, prefix)

        stmt = "select distinct(table_name) from {} {}".format(
            METADATA_TABLE_NAME,
            wc
        )

        try:
            self.cursor.execute(stmt)
            table_names = self.cursor.fetchall()
        except Exception as e:
            self.sql_error_handler(e)
            self.logger.error(str(e), exc_info=True)
            return None

        else:
            matching_types = []

            all_types = [tn[0] for tn in table_names]

            for et in all_types:
                stmt = "select distinct(entity_type) from {}".format(et)
                if fiware_servicepath == '/':
                    stmt = stmt + " WHERE {} ~* '/.*'" \
                        .format(FIWARE_SERVICEPATH)
                elif fiware_servicepath:
                    stmt = stmt + " WHERE {} ~* '{}($|/.*)'" \
                        .format(FIWARE_SERVICEPATH, fiware_servicepath)
                self.cursor.execute(stmt)
                types = [t[0] for t in self.cursor.fetchall()]
                matching_types.extend(types)

        return matching_types

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
        key = None
        if fiware_service is None:
            wc = "where table_name NOT like '\"{}%.%'".format(TENANT_PREFIX)
        else:
            # Old is prior QL 0.6.0. GH #173
            old_prefix = '{}{}'.format(TENANT_PREFIX, fiware_service.lower())
            prefix = self._et2tn("FooType", fiware_service).split('.')[0]
            wc = "where table_name like '{}.%' " \
                 "or table_name like '{}.%'".format(old_prefix, prefix)
            key = fiware_service.lower()

        stmt = "select distinct(table_name) from {} {}".format(
            METADATA_TABLE_NAME,
            wc
        )

        try:
            self.cursor.execute(stmt)
            entity_types = self.cursor.fetchall()
        except Exception as e:
            self.sql_error_handler(e)
            self.logger.error(str(e), exc_info=True)
            return None

        else:
            all_types = [et[0] for et in entity_types]

        matching_types = []
        for et in all_types:
            stmt = "select distinct(entity_type) from {} " \
                   "where entity_id = ?".format(et)
            self.cursor.execute(stmt, [entity_id, ])
            types = [t[0] for t in self.cursor.fetchall()]
            matching_types.extend(types)

        return ','.join(matching_types)

    def _compute_type(self, entity_id, attr_t, attr):

        if attr_t not in self.NGSI_TO_SQL:
            # if attribute is complex assume it as an NGSI StructuredValue
            # TODO we should support type name different from NGSI types
            # but mapping to NGSI types
            value = attr.get('value', None) or attr.get('object', None)
            sql_type = self.NGSI_TO_SQL[NGSI_TEXT]
            if isinstance(value, list):
                sql_type = self.NGSI_TO_SQL['Array']
            elif value is not None and isinstance(value, dict):
                if '@type' in value and value['@type'] == 'DateTime' \
                        and '@value' in value \
                        and self._is_iso_date(value['@value']):
                    sql_type = self.NGSI_TO_SQL[NGSI_DATETIME]
                elif self._attr_is_structured(attr):
                    sql_type = self.NGSI_TO_SQL[NGSI_STRUCTURED_VALUE]
            elif isinstance(value, int) and not isinstance(value, bool):
                sql_type = self.NGSI_TO_SQL['Integer']
            elif isinstance(value, float):
                sql_type = self.NGSI_TO_SQL['Number']
            elif isinstance(value, bool):
                sql_type = self.NGSI_TO_SQL['Boolean']
            elif self._is_iso_date(value):
                sql_type = self.NGSI_TO_SQL[NGSI_DATETIME]

            supported_types = ', '.join(self.NGSI_TO_SQL.keys())
            msg = ("'{}' is not a supported NGSI type"
                   " for Attribute:  '{}' "
                   " and id : '{}'. "
                   "Please use any of the following: {}. "
                   "Falling back to {}.")
            self.logger.warning(msg.format(
                attr_t, attr, entity_id, supported_types,
                sql_type))

            return sql_type

        else:
            # Github issue 44: Disable indexing for long string
            sql_type = self._compute_db_specific_type(attr_t, attr)

            # Github issue 24: StructuredValue == object or array
            is_list = isinstance(attr.get('value', None), list)
            if attr_t == NGSI_STRUCTURED_VALUE and is_list:
                sql_type = self.NGSI_TO_SQL['Array']
            return sql_type

    def _compute_db_specific_type(self, attr_t, attr):
        raise NotImplementedError

    def _execute_query_via_cache(self, tenant_name, key, stmt, parameters=None,
                                 ex=None):
        if self.cache:
            try:
                value = self.cache.get(tenant_name, key)
                if value:
                    return value
            except Exception as e:
                self.logger.warning("Caching not available, metadata data may "
                                    "not be consistent: " + str(e),
                                    exc_info=True)

        self.cursor.execute(stmt, parameters)
        res = self.cursor.fetchall()
        if res and self.cache:
            try:
                self._cache(tenant_name, key, res, ex)
            except Exception as e:
                self.logger.warning("Caching not available, metadata data may "
                                    "not be consistent: " + str(e),
                                    exc_info=True)
        return res

    def _is_query_in_cache(self, tenant_name, key):
        if self.cache:
            try:
                return self.cache.exists(tenant_name, key)
            except Exception as e:
                self.logger.warning("Caching not available, metadata data may "
                                    "not be consistent: " + str(e),
                                    exc_info=True)
        return False

    def _cache(self, tenant_name, key, value=None, ex=None):
        if self.cache:
            try:
                self.cache.put(tenant_name, key, value, ex)
            except Exception as e:
                self.logger.warning("Caching not available, metadata data may "
                                    "not be consistent: " + str(e),
                                    exc_info=True)

    def _remove_from_cache(self, tenant_name, key):
        if self.cache:
            try:
                self.cache.delete(tenant_name, key)
            except Exception as e:
                self.logger.warning("Caching not available, metadata data may "
                                    "not be consistent: " + str(e),
                                    exc_info=True)


class QueryCacheManager(Borg):
    cache = None

    def __init__(self):
        super(QueryCacheManager, self).__init__()
        if is_cache_available() and self.cache is None:
            try:
                self.cache = get_cache()
            except Exception as e:
                self.logger.warning("Caching not available:" + str(e),
                                    exc_info=True)

    def get_query_cache(self):
        return self.cache
