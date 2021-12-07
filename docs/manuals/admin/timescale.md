# Timescale

[Timescale][timescale] is one of the time series databases that can be
used with QuantumLeap as a back end to store NGSI entity time series.
As documented in the [Configuration section][admin.db], it is
possible to dynamically select, at runtime, which storage back end to
use (Crate or Timescale) depending on the tenant who owns the entity
being persisted. Moreover, QuantumLeap ships with tools to automate the
Timescale back end setup and generate Crate-to-Timescale migration
scripts---details in the [Data Migration section][admin.dm].

## QuantumLeap Timescale DB setup

In order to start using the Timescale back end, a working PostgreSQL
installation is required. Specifically, QuantumLeap requires
**PostgreSQL server 10 or above with the Timescale and PostGIS
extensions already installed** on it. The Docker file in the
`timescale-container/test` can be used to quickly spin up a Timescale
server back end to which QuantumLeap can connect, but for
production deployments a more sophisticated setup is likely to
be needed---e.g. configuring PostgreSQL for high availability.

Once Timescale is up and running, you will have to bootstrap the
QuantumLeap DB and perhaps you may also want to migrate some data
from Crate. QuantumLeap ships with a self-contained Python script
that can automate most of the steps in the process. The script file
is named `quantumleap-db-setup` and is located in the
`timescale-container` directory. It does these three things, in order:

1. Bootstrap the QuantumLeap database if it doesn't exist. It creates
   a database for QuantumLeap with all required extensions as well as
   an initial QuantumLeap role. If the specified QuantumLeap DB already
   exists, the bootstrap phase is skipped.
2. Run any SQL script found in the specified init directory---defaults
   to `./ql-db-init`. It picks up any `.sql` file in this directory
   tree and, in turn, executes each one in ascending alphabetical
   order, stopping at the first one that errors out, in which case
   the script exits.
3. Load any data file found in the above init directory. A data file
   is any file with a `.csv` extension found in the init directory
   tree. Each data file is expected to contain a list of records in
   the CSV format to be loaded in a table in the QuantumLeap
   database---field delimiter `,` and quoted fields must be quoted
   using a single quote char `'`. The file name without the `.csv`
   extension is taken to be the FQN of the table in which data should
   be loaded, whereas the column spec is given by the names in the
   CSV header, which is expected to be in the file. Data files are
   loaded in turn following their alphabetical order, stopping at
   the first one that errors out, in which case the script exits.

(2) and (3) are mostly relevant for data migration (more about it
in the section below), but the script can just as well be used to
execute arbitrary SQL statements. Note that the Docker compose
file mentioned earlier spins up a Timescale container (with PostGIS)
and another container that will run the script using
`timescale-container/test/ql-db-init` as init directory,
providing a working Timescale DB, complete with some tables
and test data.

## Using the Timescale back end

Once you have a Postgres+Timescale+PostGIS server with a freshly
minted QuantumLeap DB in it, you are ready to connect QuantumLeap
to the DB server. To do that, some environment variables have to
be set and a YAML file edited. The environment variables to use
are:

* `POSTGRES_HOST`: the hostname or IP address of your Timescale server.
  Defaults to `timescale` if not specified.
* `POSTGRES_PORT`: the server port to connect to, defaults to `5432`.
* `POSTGRES_DB_NAME`: the name of the QuantumLeap DB, defaults to
  `quantumleap`.
* `POSTGRES_DB_USER`: the DB user QuantumLeap should use to connect,
  defaults to `quantumleap`.
* `POSTGRES_DB_PASS`: the above user's password, defaults to `*`.
* `POSTGRES_USE_SSL`: should QuantumLeap connect to PostgreSQL using
  SSL? If so, then set this variable to any of: `true`, `yes`, `1`, `t`.
  Specify any other value or don't set the variable at all to use a
  plain TCP connection.
* `QL_CONFIG`: absolute pathname of the QuantumLeap YAML configuration
  file. If not set, the default configuration will be used where only
  the Crate back end is available. For details about how to select a
  back end and YAML configuration, refer to the [QuantumLeap Configuration][admin.db].

[admin.db]: ./configuration.md
    "QuantumLeap Configuration"
[admin.dm]: ./dataMigration.md
    "QuantumLeap Data Migration"
[postgres]: https://www.postgresql.org
    "PostgreSQL Home"
[postgis]: https://postgis.net/
    "PostGIS Home"
[timescale]: https://www.timescale.com
    "Timescale Home"
