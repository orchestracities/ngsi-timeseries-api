from datetime import datetime, timedelta, timezone
from geocoding.slf.geotypes import *
from exceptions.exceptions import AmbiguousNGSIIdError, UnsupportedOption, \
    NGSIUsageError, InvalidParameterValue
from translators import base_translator
from translators.config import SQLTranslatorConfig
from utils.common import iter_entity_attrs
from utils.jsondict import safe_get_value
from utils.maybe import maybe_map
import logging
from geocoding.slf import SlfQuery
import dateutil.parser
from typing import Any, List, Optional
from uuid import uuid4


# NGSI TYPES
# Based on Orion output because official docs don't say much about these :(
NGSI_DATETIME = 'DateTime'
NGSI_ID = 'id'
NGSI_GEOJSON = 'geo:json'
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
# TODO: replace each occurrence of these strings with the below constants.
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


# TODO: use below getters everywhere rather than entity id and type strings!

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

class SQLTranslator(base_translator.BaseTranslator):
    NGSI_TO_SQL = NGSI_TO_SQL
    config = SQLTranslatorConfig()

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

    def _prepare_data_table(self, table_name, table, fiware_service):
        raise NotImplementedError

    def _create_metadata_table(self):
        raise NotImplementedError

    def _get_isoformat(self, ms_since_epoch):
        """
        :param ms_since_epoch:
            As stated in CrateDB docs: Timestamps are always returned as long
            values (ms from epoch).
        :return: str
            The equivalent datetime in ISO 8601.
        """
        if ms_since_epoch is None:
            return "NULL"
        d = timedelta(milliseconds=ms_since_epoch)
        utc = datetime(1970, 1, 1, 0, 0, 0, 0, timezone.utc) + d
        return utc.isoformat(timespec='milliseconds')

    def _et2tn(self, entity_type, fiware_service=None):
        """
        Return table name based on entity type.
        When specified, fiware_service will define the table schema.
        To avoid conflict with reserved words,
        both schema and table name are prefixed.
        """
        et = '"{}{}"'.format(TYPE_PREFIX, entity_type.lower())
        if fiware_service:
            return '"{}{}".{}'.format(TENANT_PREFIX, fiware_service.lower(), et)
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
        # Also, an entity can't have an attribute with the same name
        # as that specified by ORIGINAL_ENTITY_COL_NAME.
        for e in entities:
            if e[NGSI_TYPE] != entity_type:
                msg = "Entity {} is not of type {}."
                raise ValueError(msg.format(e[NGSI_ID], entity_type))

            if self.TIME_INDEX_NAME not in e:
                import warnings
                msg = "Translating entity without TIME_INDEX. " \
                      "It should have been inserted by the 'Reporter'. {}"
                warnings.warn(msg.format(e))
                e[self.TIME_INDEX_NAME] = current_timex()

            if ORIGINAL_ENTITY_COL in e:
                raise ValueError(
                    f"Entity {e[NGSI_ID]} has a reserved attribute name: " +
                    "'{ORIGINAL_ENTITY_COL_NAME}'")

        # Define column types
        # {column_name -> crate_column_type}
        table = {
            'entity_id': self.NGSI_TO_SQL['Text'],
            'entity_type': self.NGSI_TO_SQL['Text'],
            self.TIME_INDEX_NAME: self.NGSI_TO_SQL[TIME_INDEX],
            FIWARE_SERVICEPATH: self.NGSI_TO_SQL['Text'],
            ORIGINAL_ENTITY_COL: self.NGSI_TO_SQL[NGSI_STRUCTURED_VALUE]
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
                    continue

                if isinstance(e[attr], dict) and 'type' in e[attr]:
                    attr_t = e[attr]['type']
                else:
                    # Won't guess the type if user did't specify the type.
                    # TODO Guess Type!
                    attr_t = NGSI_TEXT

                col = self._ea2cn(attr)
                original_attrs[col] = (attr, attr_t)

                if attr_t not in self.NGSI_TO_SQL:
                    # if attribute is complex assume it as an NGSI StructuredValue
                    # TODO we should support type name different from NGSI types
                    # but mapping to NGSI types
                    if self._attr_is_structured(e[attr]):
                        table[col] = self.NGSI_TO_SQL[NGSI_STRUCTURED_VALUE]
                    else:
                        # TODO fallback type should be defined by actual JSON type
                        supported_types = ', '.join(self.NGSI_TO_SQL.keys())
                        msg = ("'{}' is not a supported NGSI type. "
                               "Please use any of the following: {}. "
                               "Falling back to {}.")
                        self.logger.warning(msg.format(
                            attr_t, supported_types, NGSI_TEXT))

                        table[col] = self.NGSI_TO_SQL[NGSI_TEXT]

                else:
                    # Github issue 44: Disable indexing for long string
                    sql_type = self._compute_type(attr_t, e[attr])

                    # Github issue 24: StructuredValue == object or array
                    is_list = isinstance(e[attr].get('value', None), list)
                    if attr_t == NGSI_STRUCTURED_VALUE and is_list:
                        sql_type = self.NGSI_TO_SQL['Array']

                    table[attr] = sql_type

        # Create/Update metadata table for this type
        table_name = self._et2tn(entity_type, fiware_service)
        self._update_metadata_table(table_name, original_attrs)
        # Sort out data table.
        self._prepare_data_table(table_name, table, fiware_service)

        # Gather attribute values
        col_names = sorted(table.keys())
        entries = []  # raw values in same order as column names
        for e in entities:
            values = self._preprocess_values(e, table, col_names, fiware_servicepath)
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
            self.cursor.executemany(stmt, rows)
        except Exception as e:
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

    def _should_insert_original_entities(self, insert_error: Exception) -> bool:
        raise NotImplementedError

    def _insert_original_entities_in_failed_batch(
            self, table_name: str, entities: List[dict],
            insert_error: Exception):
        cols = f"{ENTITY_ID_COL}, {ENTITY_TYPE_COL}, {self.TIME_INDEX_NAME}" + \
               f", {ORIGINAL_ENTITY_COL}"
        stmt = f"insert into {table_name} ({cols}) values (?, ?, ?, ?)"
        tix = current_timex()
        batch_id = uuid4().hex
        rows = [[entity_id(e), entity_type(e), tix,
                 self._build_original_data_value(e, insert_error, batch_id)]
                for e in entities]

        self.cursor.executemany(stmt, rows)

    def _attr_is_structured(self, a):
        if a['value'] is not None and isinstance(a['value'], dict):
            self.logger.debug("attribute {} has 'value' attribute of type dict"
                              .format(a))
            return True
        return False

    # TODO this logic is too simple
    @staticmethod
    def is_text(attr_type):
        # TODO: verify: same logic in two different places!
        # The above kinda reproduces the tests done by the translator, we should
        # factor this logic out and keep it in just one place!
        return attr_type == NGSI_TEXT or attr_type not in NGSI_TO_SQL

    def _preprocess_values(self, e, table, col_names, fiware_servicepath):
        raise NotImplementedError

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

        self._create_metadata_table()

        if self.cursor.rowcount:
            # Table just created!
            persisted_metadata = {}
        else:
            # Bring translation table!
            stmt = "select entity_attrs from {} where table_name = ?"
            self.cursor.execute(stmt.format(METADATA_TABLE_NAME), [table_name])

            # By design, one entry per table_name
            res = self.cursor.fetchall()
            persisted_metadata = res[0][0] if res else {}

        if metadata.keys() - persisted_metadata.keys():
            persisted_metadata.update(metadata)
            self._store_medatata(table_name, persisted_metadata)
        # TODO: concurrency.
        # This implementation paves
        # the way to lost updates...

    def _store_medatata(self, table_name, persisted_metadata):
        raise NotImplementedError

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
        except Exception as e:
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
            clauses.append(" " + FIWARE_SERVICEPATH + " ~* '" + fiware_sp + "($|/.*)'")
        else:
            # Match prefix of fiware service path
            clauses.append(" " + FIWARE_SERVICEPATH + " = ''")

        geo_clause = self._get_geo_clause(geo_query)
        if geo_clause:
            clauses.append(geo_clause)

        where_clause = "where " + "and ".join(clauses)
        return where_clause

    def _parse_date(self, date):
        try:
            return dateutil.parser.isoparse(date.strip('\"'))
        except Exception as e:
            raise InvalidParameterValue(date, "**fromDate** or **toDate**")

    def _parse_limit(sefl, limit):
        if (not (limit is None or isinstance(limit, int))):
            raise InvalidParameterValue(limit, "limit")
        return limit

    def _parse_last_n(sefl, last_n):
        if (not (last_n is None or isinstance(last_n, int))):
            raise InvalidParameterValue(last_n, "last_n")
        return last_n

    def _get_geo_clause(self, geo_query):
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
                order_by.append("{} {}".format(self.TIME_INDEX_NAME, direction))
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
              fiware_service=None,
              fiware_servicepath=None,
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

        if last_n == 0 or limit == 0:
            return []

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
                return []

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

        result = []
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
                # Reason 1: fiware_service_path column in legacy dbs.
                logging.debug("{}".format(e))
                entities = []
            else:
                res = self.cursor.fetchall()
                col_names = [x[0] for x in self.cursor.description]
                entities = self._format_response(res,
                                                 col_names,
                                                 tn,
                                                 last_n)
            result.extend(entities)
        return result

    def query_ids(self,
                  entity_type=None,
                  from_date=None,
                  to_date=None,
                  limit=10000,
                  offset=0,
                  fiware_service=None,
                  fiware_servicepath=None):
        if limit == 0:
            return []

        where_clause = self._get_where_clause(None,
                                              from_date,
                                              to_date,
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
        stmt = ''
        for tn in sorted(table_names):
            len_tn += 1
            if len_tn != len(table_names):
                stmt += "select entity_id, entity_type, max(time_index) as time_index " \
                        "from {tn} {where_clause} " \
                        "group by entity_id, entity_type " \
                        "union all ".format(
                    tn=tn,
                    where_clause=where_clause
                )
            else:
                stmt += "select entity_id, entity_type, max(time_index) as time_index " \
                        "from {tn} {where_clause} " \
                        "group by entity_id, entity_type ".format(
                    tn=tn,
                    where_clause=where_clause
                )

        # TODO ORDER BY time_index asc is removed for the time being till we have a solution for https://github.com/crate/crate/issues/9854
        op = stmt + "limit {limit} offset {offset}".format(
            offset=offset,
            limit=limit
        )

        try:
            self.cursor.execute(op)
        except Exception as e:
            logging.debug("{}".format(e))
            entities = []
        else:
            res = self.cursor.fetchall()
            col_names = ['entity_id', 'entity_type', 'time_index']
            entities = self._format_response(res,
                                             col_names,
                                             tn,
                                             None)
        result.extend(entities)
        return result

    def _format_response(self, resultset, col_names, table_name, last_n):
        """
        :param resultset: list of query results for one entity_type
        :param col_names: list of columns affected in the query
        :param table_name: name of table where the query took place.
        :param last_n: see last_n in query method.
        :param aggr_method: True if used in the request, false otherwise.

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
        stmt = "select entity_attrs from {} " \
               "where table_name = ?".format(METADATA_TABLE_NAME)
        self.cursor.execute(stmt, [table_name])
        res = self.cursor.fetchall()

        if len(res) == 0:
            # See GH #173
            tn = ".".join([x.strip('"') for x in table_name.split('.')])
            self.cursor.execute(stmt, [tn])
            res = self.cursor.fetchall()

        if len(res) != 1:
            msg = "Cannot have {} entries in table '{}' for PK '{}'"
            msg = msg.format(len(res), METADATA_TABLE_NAME, table_name)
            self.logger.error(msg)
            raise RuntimeError(msg)

        entities = {}
        entity_attrs = res[0][0]

        if last_n:
            # LastN induces DESC order, but we always return ASC order.
            resultset = reversed(resultset)

        for r in resultset:
            for k, v in zip(col_names, r):
                if k not in entity_attrs:
                    # implementation-specific columns not representing attrs
                    # e.g. fiware-servicepath
                    continue

                e_id = r[col_names.index('entity_id')]
                e = entities.setdefault(e_id, {})
                original_name, original_type = entity_attrs[k]

                # CrateDBs and NGSI use different geo:point coordinates order.
                if original_type == NGSI_GEOPOINT:
                    if v is not None:
                        lon, lat = v
                        v = "{}, {}".format(lat, lon)

                if original_name in (NGSI_TYPE, NGSI_ID):
                    e[original_name] = v

                elif original_name == self.TIME_INDEX_NAME:
                    v = self._get_isoformat(v)
                    e.setdefault('index', []).append(v)

                else:
                    attr_dict = e.setdefault(original_name, {})

                    if original_type in (NGSI_DATETIME, NGSI_ISO8601):
                        v = self._get_isoformat(v)
                    attr_dict.setdefault('values', []).append(v)
                    attr_dict['type'] = original_type

        return [entities[k] for k in sorted(entities.keys())]

    def delete_entity(self, entity_id, entity_type=None, from_date=None,
                      to_date=None, fiware_service=None,
                      fiware_servicepath=None):
        if not entity_id:
            raise NGSIUsageError("entity_id cannot be None nor empty")

        if not entity_type:
            entity_type = self._get_entity_type(entity_id, fiware_service)

            if not entity_type:
                return 0

            if len(entity_type.split(',')) > 1:
                raise AmbiguousNGSIIdError(entity_id)

        # First delete entries from table
        table_name = self._et2tn(entity_type, fiware_service)
        where_clause = self._get_where_clause([entity_id, ],
                                              from_date,
                                              to_date,
                                              fiware_servicepath)
        op = "delete from {} {}".format(table_name, where_clause)

        try:
            self.cursor.execute(op)
        except Exception as e:
            logging.error("{}".format(e))
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
            except Exception as e:
                logging.error("{}".format(e))
                return 0
            return self.cursor.rowcount

        # Drop whole table
        try:
            self.cursor.execute("select count(*) from {}".format(table_name))
        except Exception as e:
            logging.error("{}".format(e))
            return 0
        count = self.cursor.fetchone()[0]

        op = "drop table {}".format(table_name)
        try:
            self.cursor.execute(op)
        except Exception as e:
            logging.error("{}".format(e))
            return 0

        # Delete entry from metadata table
        op = "delete from {} where table_name = ?".format(METADATA_TABLE_NAME)
        try:
            self.cursor.execute(op, [table_name])
        except Exception as e:
            logging.error("{}".format(e))

        if self.cursor.rowcount == 0 and table_name.startswith('"'):
            # See GH #173
            old_tn = ".".join([x.strip('"') for x in table_name.split('.')])
            try:
                self.cursor.execute(op, [old_tn])
            except Exception as e:
                logging.error("{}".format(e))

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

        except Exception as e:
            logging.error("{}".format(e))
            return None

        else:
            all_types = [et[0] for et in self.cursor.fetchall()]

        matching_types = []
        for et in all_types:
            stmt = "select distinct(entity_type) from {} " \
                   "where entity_id = ?".format(et)
            self.cursor.execute(stmt, [entity_id, ])
            types = [t[0] for t in self.cursor.fetchall()]
            matching_types.extend(types)

        return ','.join(matching_types)

    def _compute_type(self, attr_t, attr):
        raise NotImplementedError
