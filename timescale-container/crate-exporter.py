#!/usr/bin/env python

from argparse import ArgumentParser, ArgumentTypeError
from datetime import datetime, timedelta, timezone
import http.client
import json


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

        p.add_argument('--schema', type=ne, required=True,
                       help='Crate schema from which to export')
        p.add_argument('--table', type=ne, required=True,
                       help='Crate table from which to export')

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


class CrateQuery:

    def __init__(self, host='localhost', port=4200):
        self._conn = http.client.HTTPConnection(host, port)

    def run(self, query: str) -> dict:
        headers = {'Content-type': 'application/json'}
        sql_query = {'stmt': query}
        body = json.dumps(sql_query)

        self._conn.request('POST', '/_sql?types', body, headers)
        response = self._conn.getresponse()

        if response.status != 200:
            raise RuntimeError(f"query failed, HTTP status: {response.status}")

        data = response.read().decode()
        return json.loads(data)


class FieldConverter:

    def __init__(self, col_name, crate_type):
        self._col_name = col_name
        self._crate_type = crate_type

    def to_insert_stmt_rep(self, value) -> str:
        if value is None:
            return 'null'
        if self._col_name == 'location':
            json_rep = json.dumps(value)
            return f"ST_GeomFromGeoJSON('{json_rep}')"
        if self._col_name == 'location_centroid':
            return f"'POINT ({value[0]} {value[1]})'"
        if self._crate_type == 11:
            epoc = datetime(year=1970, month=1, day=1,
                            tzinfo=timezone(timedelta(0)))
            millis_since_epoc = epoc + timedelta(milliseconds=value)
            return f"'{millis_since_epoc}'"
        if isinstance(value, int):
            return f"{value}"
        if isinstance(value, float):
            return f"{value}"
        if isinstance(value, bool):
            return f"{value}"
        if isinstance(value, str):
            return f"'{value}'"
        if isinstance(value, dict):
            json_rep = json.dumps(value)
            return f"'{json_rep}'"

        # At this point it could only be a JSON array, puke up!
        raise RuntimeError(f"type not supported: {type(value)}")


class RowConverter:

    def __init__(self, column_names, column_types):
        self._converters = [FieldConverter(c, t)
                            for (c, t) in zip(column_names, column_types)]

    def to_insert_stmt_rep(self, row) -> str:
        vs = [c.to_insert_stmt_rep(v) for (c, v) in zip(self._converters, row)]
        vs_list = ', '.join(vs)
        return f"({vs_list})"


class InsertStatement:

    def __init__(self, schema_name, table_name, column_names, column_types):
        self._target = f'"{schema_name}"."{table_name}"'
        self._row_converter = RowConverter(column_names, column_types)
        self._cols = ', '.join([f'"{c}"' for c in column_names])

    def generate(self, rows):
        yield f"INSERT INTO {self._target}"
        yield f"({self._cols})"
        yield 'VALUES'
        for row in rows:
            yield self._row_converter.to_insert_stmt_rep(row)


def run():
    args = Args().get()
    query = f'SELECT * FROM "{args.schema}"."{args.table}" LIMIT 1'
    query_results = CrateQuery().run(query)
    insert = InsertStatement('mtlusovini', 'etdevice',
                             query_results['cols'], query_results['col_types'])
    for k in insert.generate(query_results['rows']):
        print(k)


if __name__ == "__main__":
    run()
