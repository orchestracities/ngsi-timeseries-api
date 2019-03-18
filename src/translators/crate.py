from contextlib import contextmanager
from crate import client
from crate.client import exceptions
from datetime import datetime, timedelta
from exceptions.exceptions import AmbiguousNGSIIdError, UnsupportedOption
from translators import base_translator
from utils.common import iter_entity_attrs
import logging
import os
from geocoding.slf import SlfQuery
from .crate_geo_query import from_ngsi_query

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
    NGSI_GEOJSON: 'geo_shape',
    NGSI_GEOPOINT: 'geo_point',
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
VALID_AGGR_METHODS = ['count', 'sum', 'avg', 'min', 'max']
VALID_AGGR_PERIODS = ['year', 'month', 'day', 'hour', 'minute', 'second']


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


    def get_health(self):
        """
        Return a dict of the status of crate service.

        Checkout
        https://crate.io/docs/crate/reference/en/latest/admin/system-information.html#health
        """
        health = {}

        op = "select health from sys.health order by severity desc limit 1"
        health['time'] = datetime.now().isoformat(timespec='milliseconds')
        try:
            self.cursor.execute(op)

        except exceptions.ConnectionError as e:
            msg = "{}".format(e)
            logging.debug(msg)
            health['status'] = 'fail'
            health['output'] = msg

        else:
            res = self.cursor.fetchall()
            if len(res) == 0 or res[0][0] == 'GREEN':
                # (can be empty when no tables were created yet)
                health['status'] = 'pass'
            else:
                c = res[0][0]
                health['status'] = 'warn'
                msg = "Checkout sys.health in crateDB, you have a {} status."
                health['output'] = msg.format(c)

        return health


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
        utc = datetime(1970, 1, 1, 0, 0, 0, 0) + d
        return utc.isoformat(timespec='milliseconds')


    def _et2tn(self, entity_type, fiware_service=None):
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
                now_iso = datetime.now().isoformat(timespec='milliseconds')
                e[self.TIME_INDEX_NAME] = now_iso

        # Define column types
        # {column_name -> crate_column_type}
        table = {
            'entity_id': NGSI_TO_CRATE['Text'],
            'entity_type': NGSI_TO_CRATE['Text'],
            self.TIME_INDEX_NAME: NGSI_TO_CRATE[NGSI_DATETIME],
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
                    # Won't guess the type if used did't specify the type.
                    attr_t = NGSI_TEXT

                col = self._ea2cn(attr)
                original_attrs[col] = (attr, attr_t)

                if attr_t not in NGSI_TO_CRATE:
                    # if attribute is complex assume it as an NGSI StructuredValue
                    if self._attr_is_structured(e[attr]):
                        table[col] = NGSI_TO_CRATE[NGSI_STRUCTURED_VALUE]
                    else:
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
        # NOTE. CrateDB identifiers (like column and table names) become case
        # sensitive when quoted like we do below in the CREATE TABLE statement.
        columns = ', '.join('"{}" {}'.format(cn.lower(), ct)
                            for cn, ct in table.items())
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
        p2 = ', '.join(['"{}"'.format(c.lower()) for c in col_names])
        p3 = ','.join(['?'] * len(col_names))
        stmt = "insert into {} ({}) values ({})".format(p1, p2, p3)
        self.cursor.executemany(stmt, entries)
        return self.cursor

    def _attr_is_structured(self, a):
        if a['value'] is not None and isinstance(a['value'], dict):
            self.logger.info("attribute {} has 'value' attribute of type dict"
                             .format(a))
            return True
        return False

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
            stmt = "select entity_attrs from {} where table_name = ?"
            self.cursor.execute(stmt.format(METADATA_TABLE_NAME), [table_name])
            # TODO: Make test_bc break, here we don't consider old table_name

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
            where = "where table_name ~* '\"{}{}\"[.].*'"
            op += where.format(TENANT_PREFIX, fiware_service.lower())
            # TODO: Make test_bc break, here we don't consider old table_name
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


    def _get_limit(self, limit):
        # https://crate.io/docs/crate/reference/en/latest/general/dql/selects.html#limits
        default = 10000
        if not limit:
            return default
        limit = int(limit)
        if limit < 1:
            raise ValueError("Limit should be >=1 and <= 10000.")
        return min(default, limit)


    def _get_where_clause(self, entity_ids, from_date, to_date, fiware_sp=None,
                          geo_query=None):
        clauses = []

        if entity_ids:
            ids = ",".join("'{}'".format(e) for e in entity_ids)
            clauses.append(" entity_id in ({}) ".format(ids))
        if from_date:
            clauses.append(" {} >= '{}'".format(self.TIME_INDEX_NAME,
                                                from_date))
        if to_date:
            clauses.append(" {} <= '{}'".format(self.TIME_INDEX_NAME, to_date))

        if fiware_sp:
            # Match prefix of fiware service path
            clauses.append(" "+FIWARE_SERVICEPATH+" ~* '"+fiware_sp+"($|/.*)'")
        else:
            # Match prefix of fiware service path
            clauses.append(" "+FIWARE_SERVICEPATH+" = ''")

        geo_clause = from_ngsi_query(geo_query)
        if geo_clause:
            clauses.append(geo_clause)

        where_clause = "where " + "and ".join(clauses)
        return where_clause


    def _get_order_group_clause(self, aggr_method, aggr_period, select_clause):
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
        if aggr_method:
            if aggr_period:
                # consider always ordering by entity_id also
                order_by.extend(["entity_type", "entity_id"])
                order_by.append("{} ASC".format(self.TIME_INDEX_NAME))
        else:
            order_by.append("{} ASC".format(self.TIME_INDEX_NAME))

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
              geo_query: SlfQuery=None):
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
        if entity_id and entity_ids:
            raise ValueError("Cannot use both entity_id and entity_ids params "
                             "in the same call.")

        if aggr_method and aggr_method.lower() not in VALID_AGGR_METHODS:
            raise UnsupportedOption("aggr_method={}".format(aggr_method))

        if aggr_period and aggr_period.lower() not in VALID_AGGR_PERIODS:
            raise UnsupportedOption("aggr_period={}".format(aggr_period))

        if entity_id and not entity_type:
            entity_type = self._get_entity_type(entity_id, fiware_service)

            if not entity_type:
                return []

            if len(entity_type.split(',')) > 1:
                raise AmbiguousNGSIIdError(entity_id)

        if entity_id:
            entity_ids = tuple([entity_id])

        select_clause = self._get_select_clause(attr_names,
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
                                                          select_clause)

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
            except exceptions.ProgrammingError as e:
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
        last_n = last_n or 0

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
        for r in resultset[-last_n:]:  # Improve last_n, use dec order + limit
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
            raise ValueError("entity_id cannot be None nor empty")

        if not entity_type:
            entity_type = self._get_entity_type(entity_id, fiware_service)

            if not entity_type:
                return 0

            if len(entity_type.split(',')) > 1:
                raise AmbiguousNGSIIdError(entity_id)

        # First delete entries from table
        table_name = self._et2tn(entity_type, fiware_service)
        where_clause = self._get_where_clause([entity_id,],
                                              from_date,
                                              to_date,
                                              fiware_servicepath)
        op = "delete from {} {}".format(table_name, where_clause)

        try:
            self.cursor.execute(op)
        except exceptions.ProgrammingError as e:
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
            except exceptions.ProgrammingError as e:
                logging.debug("{}".format(e))
                return 0
            return self.cursor.rowcount

        # Drop whole table
        try:
            self.cursor.execute("select count(*) from {}".format(table_name))
        except exceptions.ProgrammingError as e:
            logging.debug("{}".format(e))
            return 0
        count = self.cursor.fetchone()[0]

        op = "drop table {}".format(table_name)
        try:
            self.cursor.execute(op)
        except exceptions.ProgrammingError as e:
            logging.debug("{}".format(e))
            return 0

        # Delete entry from metadata table
        op = "delete from {} where table_name = ?".format(METADATA_TABLE_NAME)
        try:
            self.cursor.execute(op, [table_name,])
        except exceptions.ProgrammingError as e:
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
            wc = "where table_name NOT like '\"{}%.%'".format(TENANT_PREFIX)
        else:
            # See _et2tn
            prefix = '"{}{}"'.format(TENANT_PREFIX, fiware_service.lower())
            wc = "where table_name like '{}.%'".format(prefix)

        stmt = "select distinct(table_name) from {} {}".format(
            METADATA_TABLE_NAME,
            wc
        )
        try:
            self.cursor.execute(stmt)

        except exceptions.ProgrammingError as e:
            logging.debug("{}".format(e))
            return None

        else:
            all_types = [et[0] for et in self.cursor.fetchall()]

        matching_types = []
        for et in all_types:
            stmt = "select distinct(entity_type) from {} " \
                   "where entity_id = ?".format(et)
            self.cursor.execute(stmt, [entity_id,])
            types = [t[0] for t in self.cursor.fetchall()]
            matching_types.extend(types)

        return ','.join(matching_types)


def _adjust_gh_44(attr_t, attr, db_version):
    """
    Github issue 44: Disable indexing for long string
    """
    crate_t = NGSI_TO_CRATE[attr_t]
    if attr_t == NGSI_TEXT:
        attr_v = attr.get('value', '')
        is_long = attr_v is not None and len(attr_v) > 32765
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
