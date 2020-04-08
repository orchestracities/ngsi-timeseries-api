# Configuration

## Environment variables

To configure QuantumLeap you can use the following environment variables:

| Variable           | Description             | 
| -------------------|-------------------------|
| `CRATE_HOST`       | CrateDB Host            |
| `CRATE_PORT`       | CrateDB Port            |
| `POSTGRES_HOST`    | PostgreSQL Host         |
| `POSTGRES_PORT`    | PostgreSQL Port         |
| `POSTGRES_DB_NAME` | PostgreSQL default db   |
| `POSTGRES_DB_USER` | PostgreSQL user         |
| `POSTGRES_DB_PASS` | PostgreSQL password     |
| `POSTGRES_USE_SSL` | `t` or `f` enable SSL   |
| `REDIS_HOST`       | Redis Host              |
| `REDIS_PORT`       | Redis Port              |
| `USE_GEOCODING`    | `True` or `False` enable or disable geocoding |
| `QL_CONFIG`        | Pathname for tenant  configuration  |
| `LOGLEVEL`         | define the log level for all services (`DEBUG`, `INFO`, `WARNING` , `ERROR`)      |

## Database selection per different tenant

QuantumLeap can use different time series databases to persist and
query NGSI data. Currently both [CrateDB][crate] and [Timescale][timescale]
are supported as back ends, even though query functionality is
not yet available for Timescale.

If no configuration is provided QuantumLeap assumes CrateDB is
the back end to use and will store all incoming NGSI data in it.
However, different back ends can be configured for specific tenants
through a YAML configuration file. To use this feature, you have
to set the environment variable below:

* `QL_CONFIG`: absolute pathname of the QuantumLeap YAML configuration
  file. If not set, the default configuration will be used where only
  the Crate back end is available.

The YAML configuration file specifies what back end to use for which
tenant as well as the default back end to use for any other tenant
not explicitly mentioned in the file. Here's an example YAML
configuration:

    tenants:
        t1:
            backend: Timescale
        t2:
            backend: Crate
        t3:
            backend: Timescale

    default-backend: Crate

With this configuration, any NGSI entity coming in for tenant `t1`
or `t3` will be stored in Timescale whereas tenant `t2` will use
Crate. Any tenant other than `t1`, `t2`, or `t3` gets the default
Crate back end.




[crate]: ./crate.md
    "QuantumLeap Crate"
[timescale]: ./timescale.md
    "QuantumLeap Timescale"
