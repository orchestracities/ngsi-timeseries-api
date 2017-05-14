from benchmark.base_translator import BaseTranslator
from benchmark.common import ATTR_TO_TYPE
from influxdb import InfluxDBClient


class InfluxTranslator(BaseTranslator):

    # These defaults are to be used with the influx run by the benchmark/docker-compose.yml file.
    def __init__(self, host="localhost", port=8086, db_name="ngsi-tsdb"):
        super(InfluxTranslator, self).__init__(host, port, db_name)
        self.client = InfluxDBClient(host, port, 'root', 'root')


    def setup(self):
        self.client.create_database(self.db_name)


    def dispose(self):
        self.client.drop_database(self.db_name)


    def translate_from_ngsi(self, entities):
        """
        :param entities: iterable of dicts (NGSI JSON Entity Representation)
        :return: iterator on InfluxDB JSON representation of measurement points. I.e, NGSI to InfluxDB.
        """
        for ent in entities:
            for attr in ent:
                if attr in ("id", "type", self.TIME_INDEX_NAME):
                    continue
                p = {
                    "measurement": attr,
                    "time": ent[self.TIME_INDEX_NAME],
                    "tags": {
                        "entity_type": ent["type"],
                        "entity_id": ent["id"]
                    },
                    "fields": {
                        "value": ent[attr]["value"]
                    }
                }
                yield p


    def translate_to_ngsi(self, resultsets):
        """
        :param resultsets: list(ResultSet)
        :return: iterable(dict). I.e, InfluxDB results to NGSI entities (in JSON Entity Representation).
        """
        references = {}
        for rs in resultsets:
            for k, seriepoints in rs.items():
                attr = k[0]
                for p in seriepoints:  # This level of for evidences why this is just for small testing purposes
                    e = references.setdefault(p["time"],
                                              {"type": p['entity_type'],
                                               "id": p['entity_id'],
                                               self.TIME_INDEX_NAME: p["time"]})
                    e[attr] = {"type": ATTR_TO_TYPE[attr], "value": p['value']}
        return references.values()


    def insert(self, entities):
        """
        https://docs.influxdata.com/influxdb/v1.2/guides/writing_data/

        :param entities: iterable of dicts (NGSI JSON Entity Representation)
        :return: result of native insert call
        """
        points = list(self.translate_from_ngsi(entities))
        result = self.client.write_points(points, database=self.db_name)
        return result


    def _query(self, select, measurements, where_clause):
        """
        When querying InfluxDB, remember that there must be at least one field in the select to get results, using only
        time/tags will not return data.

        Queries in Influx are done first by measurement, then of course you can filter.

        More info: https://docs.influxdata.com/influxdb/v1.2/query_language/data_exploration/

        :param unicode select:
        :param unicode measurements:
        :param unicode where_clause: Used to filter. Defaults to empty, so if used, include the WHERE prefix as shown.
        E.g: where_clause = "WHERE entity_id = '1'"

        :return: ?
        """
        # Be careful when selecting multiple measurements in the same query. If fields names are the same, influxDB
        # will not automatically rename those columns, it will preserve only one.
        query = ""
        for m in measurements:
            query += "select {} from {} {};".format(select, m, where_clause)

        return self.client.query(query, database=self.db_name)


    def query(self, attr_names=None, entity_id=None):
        """
        Helper to query entity data from InfluxDB, "gathering" data from given measurements.

        :param unicode attr_names:
        :param unicode entity_id:

        Queries will be restricted to a single entity_type, because semantics of attributes among different entity types
        might be different.

        :returns: dict{}
        """
        if not attr_names:
            rs = self.client.query("SHOW MEASUREMENTS", database=self.db_name)
            measurements = [m[0] for m in rs.raw['series'][0]['values']]
        else:
            measurements = attr_names

        where_clause = "" if not entity_id else "WHERE entity_id = '{}'".format(entity_id)
        result = self._query("*", measurements, where_clause)

        if not isinstance(result, list):
            result = [result]

        entities = self.translate_to_ngsi(result)
        return entities


    def average(self, attr_name, entity_id=None):
        """
        There are many types of averages:
            - historical for 1 entity
            - historical for N entities
            - last measurement value for N entities
        This will be a simple average among all attr_float values in the records.
        :param db_client:
        :param db_name:
        :param entity_id: (optional). If given, calculates the average only for the matching entity_id.
        :return:
        """
        where_clause = "WHERE entity_id = '{}'".format(entity_id) if entity_id else ''
        res = self._query('MEAN("value")', measurements=['attr_float'], where_clause=where_clause)
        mean = list(res.get_points())[0]['mean']
        return mean
