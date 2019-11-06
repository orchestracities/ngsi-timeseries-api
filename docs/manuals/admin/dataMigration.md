# Data Migration

A few tools are available to assist with migrating data to QuantumLeap.

## Migrating from QuantumLeap Crate to Timescale

QuantumLeap provides a self-contained Python script to help with
migrating tables from a QuantumLeap CrateDB database to a QuantumLeap
Timescale database. The script is located in the `timescale-container`
directory and is called `crate-exporter.py`.
It exports rows in a given Crate table and generates, on `stdout`,
all the SQL statements needed to import that data into Timescale.
These include creating a corresponding schema, table and hypertable
in PostgreSQL as needed. Note that the script generates DDL statements
that, when executed, will result in the exact same table structures
the QuantumLeap Timescale back end would have generated on seeing
NGSI entities corresponding to the rows stored in the Crate table.

Here's an example usage

    $ python crate-exporter.py --schema mtyoutenant --table etdevice \
        > mtyoutenant.etdevice-import.sql

where we export all the rows in the Crate table `mtyoutenant.etdevice`.
The generated file contains all the SQL statements to recreate the
table and insert the data in Timescale. You may want to put this file
in the `quantumleap-db-setup` script's init directory so that data
are migrated automatically for you when you bootstrap the QuantumLeap
DB on Timescale as explained in the [Timescale section][ts-admin].

By default the script exports all the rows in the Crate table, but
you can also use the `--query` argument to specify a query to select
only a subset of interest as shown below:

    $ python crate-exporter.py --schema mtyoutenant --table etdevice --query \
        "SELECT * FROM mtyoutenant.etdevice where time_index > '2019-04-15';"


[ts-admin]: ./timescale.md
    "QuantumLeap Timescale"
