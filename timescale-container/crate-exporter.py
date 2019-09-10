#!/usr/bin/env python

"""
QuantumLeap Timescale migration script.

This script exports rows in a given Crate table and generates, on stdout,
all the SQL statements you need to import that data into Timescale. These
include creating a corresponding schema, table and hypertable in Postgres
as needed. By default we export all rows in the Crate table, but you can
also use the --query argument to specify a query to select only a subset
of interest.

Assumptions
-----------
1. Python v3.6 or higher. By default, we pick up the Python interpreter
   returned by the `env` command. If that isn't suitable, you should run
   this script with a v >= 3.6 interpreter.
"""

from argparse import ArgumentParser, ArgumentTypeError
from datetime import datetime, timedelta, timezone
import http.client
import json
from typing import Iterable


class Args:
    """Command line arguments parser."""

    @staticmethod
    def _non_empty_string(x: str) -> str:
        if x is None or x.strip() == '':
            raise ArgumentTypeError("must not be empty or just white space")
        return x

    def _build_parser(self) -> ArgumentParser:
        p = ArgumentParser(description='QuantumLeap Crate export script.')
        ne = self._non_empty_string

        p.add_argument('--schema', type=ne, required=False,
                       help='Crate schema from which to export')
        p.add_argument('--table', type=ne, required=True,
                       help='Crate table from which to export')
        p.add_argument('--query', type=ne, required=False,
                       help='Crate query to fetch the data to export')

        p.add_argument('--host', type=ne, required=False,
                       default='localhost',
                       help='Hostname of the Crate server')
        p.add_argument('--port', type=int, required=False,
                       default=4200,
                       help='Port number of the Postgres server')

        return p

    def __init__(self):
        self._parser = self._build_parser()

    def get(self):
        """
        Return the parsed command line arguments if the parser succeeds,
        raise an exception otherwise.
        """
        return self._parser.parse_args()


class CrateSql:
    """Crate SQL utilities."""

    @staticmethod
    def to_string(x) -> str:
        """
        Convert the input into a Crate string.
        E.g. input   ~~~> 'input'
        """
        v = str(x)  # TODO consider escaping?
        return f"'{v}'"

    @staticmethod
    def to_quoted_identifier(x) -> str:
        """
        Convert the input into a Crate quoted identifier.
        E.g. input   ~~~> "input"
        """
        v = str(x)  # TODO consider escaping?
        return f'"{v}"'


class CrateTableIdentifier:
    """
    Represents a Crate table identifier.
    """

    def __init__(self, table_name: str, schema_name: str = 'doc'):
        """
        Create a table identifier.

        :param schema_name: the (unquoted) name of the schema the table is in,
            defaults to 'doc'---see Crate docs, excuse the pun!
        :param table_name: the (unquoted) table name.
        """
        self._table_name = table_name
        self._schema_name = schema_name

    def schema_name(self) -> str:
        """
        :return: schema name as quoted identifier.
        """
        return CrateSql.to_quoted_identifier(self._schema_name)

    def table_name(self) -> str:
        """
        :return: table name as quoted identifier.
        """
        return CrateSql.to_quoted_identifier(self._table_name)

    def fqn(self) -> str:
        """
        :return: table fully qualified name in the format: "schema"."table"
        """
        return f"{self.schema_name()}.{self.table_name()}"


class CrateTable:
    """
    Holds table spec of the Crate table from which to export data.
    """

    TIME_INDEX_COLUMN_NAME = 'time_index'
    LOCATION_COLUMN_NAME = 'location'
    CENTROID_COLUMN_NAME = 'location_centroid'

    def __init__(self, table_identifier: CrateTableIdentifier,
                 column_names: list, column_type_codes: list):
        """
        Specify a Crate table structure.
        See "Column Types" section of:
        - https://crate.io/docs/crate/reference/en/latest/interfaces/http.html

        :param table_identifier: the table fully qualified name.
        :param column_names: the list of (unquoted) column names.
        :param column_type_codes: the list of corresponding Crate column types,
            given in the same order as the column names.
        """
        self._identifier = table_identifier
        self._col_names = column_names
        self._col_type_codes = column_type_codes

    def identifier(self):
        return self._identifier

    def zip_with_col_specs(self, f):
        zs = zip(self._col_names, self._col_type_codes)
        return [f(name, crate_type) for (name, crate_type) in zs]


class SqlConverter:
    """
    Convert Crate types/values to the corresponding Postgres types/values
    for use in the import script.
    """

    @staticmethod
    def json_geom(value: dict) -> str:
        json_rep = json.dumps(value)
        return f"ST_GeomFromGeoJSON('{json_rep}')"

    @staticmethod
    def centroid(value: list) -> str:
        return f"'POINT ({value[0]} {value[1]})'"

    @staticmethod
    def timestamp(value: int) -> str:
        epoch = datetime(year=1970, month=1, day=1,
                         tzinfo=timezone(timedelta(0)))
        millis_since_epoch = epoch + timedelta(milliseconds=value)
        return f"'{millis_since_epoch.isoformat()}'"

    @staticmethod
    def jason(value: dict) -> str:
        json_rep = json.dumps(value)
        return f"'{json_rep}'"

    @staticmethod
    def text(value: str) -> str:
        return f"'{value}'"

    @staticmethod
    def as_is(value) -> str:
        return f"{value}"

    @staticmethod
    def conversion_map(col_name, crate_type):
        if col_name == CrateTable.TIME_INDEX_COLUMN_NAME:
            return 'timestamp WITH TIME ZONE NOT NULL', SqlConverter.timestamp
            # hyper-table requires a non-null time index
        if col_name == CrateTable.LOCATION_COLUMN_NAME:
            return 'geometry', SqlConverter.json_geom
        if col_name == CrateTable.CENTROID_COLUMN_NAME:
            return 'geometry', SqlConverter.centroid

        # See:
        # https://crate.io/docs/crate/reference/en/latest/interfaces/http.html
        # for the complete list; this script doesn't support all possible types
        # only those used by QuantumLeap.
        if crate_type == 3:  # Boolean
            return 'boolean', SqlConverter.as_is
        if crate_type == 4:  # Text
            return 'text', SqlConverter.text
        if crate_type in [6, 7]:  # Double Precision, Real
            return 'float', SqlConverter.as_is
        if crate_type in [8, 9, 10]:  # Smallint, Integer, Bigint
            return 'bigint', SqlConverter.as_is
        if crate_type == 11:  # Timestamp
            return 'timestamp WITH TIME ZONE', SqlConverter.timestamp
        if crate_type in [12, 15]:  # Object, Unchecked Object
            return 'jsonb', SqlConverter.jason
        if crate_type in [13, 14]:  # GeoPoint, GeoShape
            return 'geometry', SqlConverter.json_geom
        if isinstance(crate_type, list):
            # 100 Array, e.g. [100, 4] for array of text
            return 'jsonb', SqlConverter.jason

        raise RuntimeError(f"unsupported Crate type: {crate_type}")

    def __init__(self, col_name: str, crate_type):
        self._col_name = col_name
        t, f = SqlConverter.conversion_map(col_name, crate_type)
        self._pg_type = t
        self._value_converter = f

    def column_name(self):
        """
        :return: the (unquoted) column name.
        """
        return self._col_name

    def pg_type(self) -> str:
        """
        :return: the mapped Postgres type.
        """
        return self._pg_type

    def convert(self, value) -> str:
        """
        Convert the given Crate value to a string value to be added to the
        import script.

        :param value: the Crate value.
        :return: the Postgres value to insert.
        """
        if value is None:
            return 'null'
        return self._value_converter(value)


class SqlGenerator:
    """
    Poor man approach to SQL generation.
    """

    @staticmethod
    def select_all_from_src_table(src_table: CrateTableIdentifier):
        fqn = src_table.fqn()
        return f"SELECT * FROM {fqn} LIMIT 1000000000;"
    # NOTE if you don't specify a limit, Crate will use a default of 10,000.

    def __init__(self, src_table: CrateTable):
        self._table = src_table
        self._converters = src_table.zip_with_col_specs(SqlConverter)

    def _column_specs(self):
        for c in self._converters:
            quoted_name = CrateSql.to_quoted_identifier(c.column_name())
            yield quoted_name, c.pg_type()

    def _data_vector(self, row) -> str:
        vs = [c.convert(v) for (c, v) in zip(self._converters, row)]
        joined = ', '.join(vs)
        return f"({joined})"

    def create_target_schema(self):
        quoted_schema = self._table.identifier().schema_name()
        return f"CREATE SCHEMA IF NOT EXISTS {quoted_schema};"

    def create_target_table(self):
        table_fqn = self._table.identifier().fqn()
        cs = [f"{n} {t}" for (n, t) in self._column_specs()]
        cols = ', '.join(cs)
        return f"CREATE TABLE IF NOT EXISTS {table_fqn} ({cols});"

    def add_target_table_columns(self):
        table_fqn = self._table.identifier().fqn()
        cs = [f"ADD COLUMN IF NOT EXISTS {n} {t}"
              for (n, t) in self._column_specs()]
        cols = ', '.join(cs)
        return f"ALTER TABLE {table_fqn} {cols};"

    def create_target_hypertable(self):
        fqn = CrateSql.to_string(self._table.identifier().fqn())
        tix = CrateSql.to_string(CrateTable.TIME_INDEX_COLUMN_NAME)
        return f"SELECT create_hypertable({fqn}, {tix}, if_not_exists => true);"

    def import_script_lines(self, exported_rows: Iterable) -> Iterable[str]:
        """
        Generate the script to create the target table in Postgres and
        insert into it the data exported from Crate.
        Note the use of streaming to generate the script in constant space.
        This is important since the exported data stream may be too big to
        fit into memory.

        :param exported_rows: a stream of rows exported from Crate.
        :return: a stream of lines making up the Postgres import script.
        """
        yield self.create_target_schema()
        yield self.create_target_table()
        yield self.add_target_table_columns()
        yield self.create_target_hypertable()

        yield f"INSERT INTO {self._table.identifier().fqn()}"
        cols = ', '.join([n for (n, t) in self._column_specs()])
        yield f"({cols})"
        yield 'VALUES'
        for k, row in enumerate(exported_rows):
            vs = self._data_vector(row)
            if k == 0:
                yield vs
            else:
                yield ', ' + vs
        yield ';'


class CrateClient:
    """
    Rudimentary Crate client which uses the Crate HTTP interface.
    """

    def __init__(self, host='localhost', port=4200):
        self._conn = http.client.HTTPConnection(host, port)

    def run(self, sql: str) -> dict:
        headers = {'Content-type': 'application/json'}
        sql_msg = {'stmt': sql}
        body = json.dumps(sql_msg)

        self._conn.request('POST', '/_sql?types', body, headers)
        response = self._conn.getresponse()

        if response.status != 200:
            raise RuntimeError(f"Failed with HTTP status: {response.status}")

        data = response.read().decode()
        return json.loads(data)


def lookup_create_query(args, table: CrateTableIdentifier):
    if args.query:
        return args.query
    return SqlGenerator.select_all_from_src_table(table)


def run():
    args = Args().get()

    table_identifier = CrateTableIdentifier(args.table, args.schema)

    query = lookup_create_query(args, table_identifier)
    query_results = CrateClient().run(query)

    table = CrateTable(table_identifier,
                       query_results['cols'], query_results['col_types'])
    generator = SqlGenerator(table)

    for k in generator.import_script_lines(query_results['rows']):
        print(k)

    # NOTE. Beware of large datasets!
    # While in principle we could handle a humongous number of rows, those
    # would have to be streamed. Sadly the Crate guys decided to return
    # JSON from the HTTP interface, which means we'll have to suck into
    # memory all the rows at once with query_results['rows']. Yuck!


if __name__ == "__main__":
    run()
