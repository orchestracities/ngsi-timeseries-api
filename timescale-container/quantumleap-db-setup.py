#!/usr/bin/env python

"""
QuantumLeap Timescale database boot/initialise/load script.
(Adapted from: https://github.com/c0c0n3/ome-odd-n-ends/blob/master/nixos/pkgs/omero/db-bootstrap.py)

This script does these three things, in order:

1. Bootstrap the QuantumLeap database if it doesn't exist. We create
   a database for QuantumLeap with all required extensions as well as
   an initial QuantumLeap role. If the specified QuantumLeap DB already
   exists, we skip the bootstrap phase.
2. Run any SQL script found in the specified init directory---defaults
   to `./ql-db-init`. We pick up any '.sql' file in this directory tree
   and, in turn, execute each one in ascending alphabetical order, stopping
   at the first one that errors out, in which case this script exits.
3. Load any data file found in the above init directory. A data file is
   any file with a '.csv' extension found in the init directory tree. We
   expect each data file to contain a list of records in the CSV format
   to be loaded in a table in the QuantumLeap database---field delimiter
   ',' and quoted fields must be quoted using a single quote char "'".
   The file name without the '.csv' extension is taken to be the FQN of
   table where data should be loaded in whereas the column spec is given
   by the names in the CSV header, which is expected to be there!
   Data files get loaded in turn following their alphabetical order,
   stopping at the first one that errors out, in which case this script
   exits.

Assumptions
-----------
1. Python v3.6 or higher. By default, we pick up the Python interpreter
   returned by the `env` command. If that isn't suitable, you should run
   this script with a v >= 3.6 interpreter.
2. Postgres `psql` command is in the PATH and is compatible with Postgres
   server v10 or higher.
3. Scripts and data files are encoded in utf8.

Notes
-----
1. SSL connections. This script interacts with Posgres through `psql`.
Since we don't specify any SSL mode explicitly, the default of `prefer`
will be used. Under this mode, `psql` will first attempt to establish
an SSL connection with the server and fall back to plain TCP if SSL
can't be used---this may happen if either or both the server and the
client don't have OpenSSL installed or if the server isn't configured
to use SSL for connections from the client host or if the server isn't
configured to use SSL at all.
"""

from argparse import ArgumentParser, ArgumentTypeError
import os
from subprocess import Popen, PIPE, CalledProcessError
from string import Template
import sys
from time import sleep


def is_not_blank(x: str) -> bool:
    """Are there any non-blank chars in the input string?"""
    return bool(x and x.strip())


def files_in_asc_order(base_dir: str, extension: str) -> [str]:
    """
    Recursively grab all files in a directory having a specified extension
    and return them in ascending alphabetical order.

    :param base_dir: path of the directory to search.
    :param extension: the file extension.
    :return: list of absolute file paths having that extension.
    """
    files = []
    for root, d, fs in os.walk(base_dir):
        for f in fs:
            if f.endswith(extension):
                files.append(os.path.join(root, f))

    return sorted(files)


def file_name_without_extension(path: str) -> str:
    """Return the file name path component without its extension, if any."""
    base = os.path.basename(path)
    name, ext = os.path.splitext(base)
    return name
# NOTE. Above is always safe as:
#   os.path.splitext('x')     ~> ('x', '')
#   os.path.splitext('')      ~> ('', '')
# Also note:
#   os.path.splitext('a.b.c') ~> ('a.b', '.c')


def read_first_line(path: str) -> str:
    """Read the first line from the given file."""
    with open(path, encoding='utf8') as f:
        return f.readline()


class Args:
    """Command line arguments parser."""

    @staticmethod
    def _non_empty_string(x: str) -> str:
        if x is None or x.strip() == '':
            raise ArgumentTypeError("must not be empty or just white space")
        return x

    def _build_parser(self) -> ArgumentParser:
        p = ArgumentParser(
            description='QuantumLeap database bootstrap script.')
        ne = self._non_empty_string

        p.add_argument('--ql-db-name', type=ne, required=False,
                       default='quantumleap',
                       help='QuantumLeap database name')
        p.add_argument('--ql-db-user', type=ne, required=False,
                       default='quantumleap',
                       help='QuantumLeap database role name')
        p.add_argument('--ql-db-pass', type=ne, required=False,
                       default='*',
                       help='QuantumLeap database role password')

        p.add_argument('--ql-db-init-dir', type=ne, required=False,
                       default='ql-db-init',
                       help='QuantumLeap database SQL init scripts dir path')

        p.add_argument('--pg-host', type=ne, required=False,
                       default='localhost',
                       help='Hostname of the Postgres server')
        p.add_argument('--pg-port', type=int, required=False,
                       default='5432',
                       help='Port number of the Postgres server')
        p.add_argument('--pg-username', type=ne, required=False,
                       default='postgres',
                       help='Postgres admin username')
        p.add_argument('--pg-pass', type=str, required=False,
                       default='',
                       help='Postgres admin password')

        return p

    def __init__(self):
        self._parser = self._build_parser()

    def get(self):
        """
        Return the parsed command line arguments if the parser succeeds,
        raise an exception otherwise.
        """
        return self._parser.parse_args()


class PgSql:
    """PgSql utilities."""

    @staticmethod
    def escape_single_quote(x: str) -> str:
        """
        Single quote escaping for Postres strings: replace any single quote
        with two single quotes. E.g. x'y'z ~~~> x''y''z
        """
        return x.replace("'", "''")

    @staticmethod
    def escape_double_quote(x: str) -> str:
        """
        Double quote escaping for Postres quoted identifiers: replace any
        double quote with two double quotes. E.g. x"y"z ~~~> x""y""z
        """
        return x.replace('"', '""')

    @staticmethod
    def to_string(x) -> str:
        """
        Convert the input into a Postgres string, escaping if needed.
        E.g. input   ~~~> 'input'
             in'put  ~~~> 'in''put'
        """
        escaped = PgSql.escape_single_quote(str(x))
        return "'{0}'".format(escaped)

    @staticmethod
    def to_quoted_identifier(x) -> str:
        """
        Convert the input into a Postgres quoted identifier, escaping if
        needed.
        E.g. input   ~~~> "input"
             in"put  ~~~> "in""put"
        """
        escaped = PgSql.escape_double_quote(str(x))
        return '"{0}"'.format(escaped)


class CreateDb:
    """
    SQL to create QuantumLeap database and role as well as
    enabling the required PostGIS and Timescale extensions.
    """

    _sql_template = Template('''
CREATE ROLE ${db_user}
    LOGIN PASSWORD ${db_pass};

CREATE DATABASE ${db_name}
    OWNER ${db_user}
    ENCODING 'UTF8';

\connect ${db_name}

CREATE EXTENSION IF NOT EXISTS postgis CASCADE;
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
''')
# NOTE. We connect to the QL DB so that the extensions get created in the
# QL DB. You'll need to be Postgres super user to create those extensions.
# NOTE. Use psql stdin to execute the above statements rather than -c.
# In fact, you can't mix SQL and psql meta-commands within a -c option.

    @staticmethod
    def sql(db_name, db_user, db_pass) -> str:
        """Produce the SLQ to bootstrap QuantumLeap database."""
        return CreateDb._sql_template.substitute(
            db_name=PgSql.to_quoted_identifier(db_name),
            db_user=PgSql.to_quoted_identifier(db_user),
            db_pass=PgSql.to_string(db_pass)
        )


class DbExist:
    """SQL to check if a database exists."""

    _sql_template = Template('''
SELECT 1 FROM pg_database WHERE datname = ${db_name};
''')

    @staticmethod
    def sql(db_name) -> str:
        """Produce the SLQ to check if a database exists."""
        return DbExist._sql_template.substitute(
            db_name=PgSql.to_string(db_name))


class LoadFromCsv:
    """Psql SQL meta-command to load data from CSV."""

    _sql_template = Template(
        "\\COPY ${table}(${columns}) FROM STDIN " +
        "WITH (FORMAT CSV, HEADER, DELIMITER ',', QUOTE '''');"
    )

    @staticmethod
    def sql(table, columns) -> str:
        """Produce the SLQ meta-command."""
        return LoadFromCsv._sql_template.substitute(
            table=table, columns=columns)


class Psql:
    """Use the psql command to execute SQL statements."""

    @staticmethod
    def _build_connection_uri(dbname, hostname, port, username, password):
        return f'postgres://{username}:{password}@{hostname}:{port}/{dbname}'

    def __init__(self, dbname, hostname, port, username, password):
        """
        Create a new instance to execute SQL statements.
        Input parameters determine how to connect to the Postgres server.
        """
        self._cmd = [
            'psql',
            Psql._build_connection_uri(dbname, hostname, port,
                                       username, password),
            '-w',  # never prompt for passwords
            '-t',  # output tuples only
            '-q',  # quiet
        ]
        self._stdin = PIPE
        self._stdin_text = None

    def with_script_file(self, file_path: str) -> 'Psql':
        self._cmd += ['-f', file_path]
        return self

    def with_command(self, statements: str) -> 'Psql':
        self._cmd += ['-c', statements]
        return self

    def with_stdin_from_file(self, file_path: str) -> 'Psql':
        self._stdin = open(file_path, encoding='utf8')
        return self

    def with_stdin_from_mem(self, text: str) -> 'Psql':
        self._stdin = PIPE
        self._stdin_text = text
        return self

    def _check_outcome(self, ret_code, out, err):
        if is_not_blank(err):
            print(err, file=sys.stderr)
        if ret_code != 0:
            raise CalledProcessError(cmd=self._cmd, returncode=ret_code)
        return out

    def run(self) -> str:
        """Run the psql command and return its stdout."""
        # Use pipes to avoid passwords leaking into log files.
        with Popen(self._cmd,
                   stdin=self._stdin, stdout=PIPE, stderr=PIPE,
                   encoding='utf8') as psql:
            out, err = psql.communicate(input=self._stdin_text)
            return self._check_outcome(psql.returncode, out, err)


class DbExistCmd:
    """Check if a database exists."""

    def __init__(self, args):
        self._args = args

    def _psql(self):
        return Psql(dbname='',
                    hostname=self._args.pg_host,
                    port=self._args.pg_port,
                    username=self._args.pg_username,
                    password=self._args.pg_pass)

    def db_exist(self, db_name: str) -> bool:
        """Check if there's a database having the specified name."""
        query = DbExist.sql(db_name)
        out = self._psql().with_stdin_from_mem(query).run()
        return out.find('1') != -1


class DbBootstrapCmd:
    """Bootstrap the QuantumLeap database."""

    def __init__(self, args):
        self._args = args

    def _psql(self):
        return Psql(dbname='',
                    hostname=self._args.pg_host,
                    port=self._args.pg_port,
                    username=self._args.pg_username,
                    password=self._args.pg_pass)

    def _log_start(self):
        ql_db = self._args.ql_db_name
        print(f'Bootstrapping QuantumLeap DB: {ql_db}')

    def _log_skip(self):
        ql_db = self._args.ql_db_name
        print(f'Skipping bootstrap as DB already exists: {ql_db}')

    def _log_done(self):
        ql_db = self._args.ql_db_name
        print(f'Successfully bootstrapped DB: {ql_db}')

    def _should_run(self):
        return not DbExistCmd(self._args).db_exist(self._args.ql_db_name)

    def run(self):
        """Bootstrap the DB if it doesn't exist, do nothing otherwise."""
        self._log_start()
        if self._should_run():
            statements = CreateDb.sql(self._args.ql_db_name,
                                      self._args.ql_db_user,
                                      self._args.ql_db_pass)
            self._psql().with_stdin_from_mem(statements).run()
            self._log_done()
        else:
            self._log_skip()


class DbInitCmd:
    """Run any SQL init scripts."""

    def __init__(self, args):
        self._args = args

    def _psql(self):
        return Psql(dbname=self._args.ql_db_name,
                    hostname=self._args.pg_host,
                    port=self._args.pg_port,
                    username=self._args.ql_db_user,
                    password=self._args.ql_db_pass)

    def run(self):
        """
        Run any SQL scripts found in the init directory against the freshly
        minted QuantumLeap DB and using the QuantumLeap role.
        Scripts get run in ascending alphabetical order, stopping at the first
        one that errors out.
        Do nothing if the init directory doesn't exist or contains no file
        with a '.sql' extension.
        """
        for path in files_in_asc_order(self._args.ql_db_init_dir, '.sql'):
            print(f'Running init script: {path}')
            out = self._psql().with_script_file(path).run()
            print(out)


class DbLoadCmd:
    """Load any CSV data."""

    def __init__(self, args):
        self._args = args

    def _psql(self):
        return Psql(dbname=self._args.ql_db_name,
                    hostname=self._args.pg_host,
                    port=self._args.pg_port,
                    username=self._args.ql_db_user,
                    password=self._args.ql_db_pass)

    def run(self):
        """
        Load any CSV file found in the init directory into the QuantumLeap DB
        using the QuantumLeap role.
        Data files get loaded in ascending alphabetical order, stopping at the
        first one that errors out.
        Do nothing if the init directory doesn't exist or contains no file
        with a '.csv' extension.
        """
        for path in files_in_asc_order(self._args.ql_db_init_dir, '.csv'):
            print(f'Loading data from: {path}')

            name = file_name_without_extension(path)
            header = read_first_line(path)
            copy = LoadFromCsv.sql(table=name, columns=header)
            out = self._psql()\
                .with_command(copy)\
                .with_stdin_from_file(path)\
                .run()

            print(out)


def run():
    count = 0
    retry = True
    while retry and count < 10:
        try:
            args = Args().get()
            DbBootstrapCmd(args).run()
            DbInitCmd(args).run()
            DbLoadCmd(args).run()
            retry = False
        except CalledProcessError as cpe:
            # Rewrite error message to avoid leaking passwords into log files.
            msg = 'Command `{0}` did not complete successfully. Exit status: {1}' \
                .format(cpe.cmd[0], cpe.returncode)
            print(msg, file=sys.stderr)
            if cpe.output is not None:
                print(str(cpe.output), file=sys.stderr)
            count = count + 1
            sleep(5)
    if not retry:
        sys.exit(64)


if __name__ == "__main__":
    run()
