# Configuration

## Environment variables

To configure QuantumLeap you can use the following environment variables:

| Variable           | Description             |
| -------------------|-------------------------|
| `CRATE_HOST`       | CrateDB Host            |
| `CRATE_PORT`       | CrateDB Port            |
| `CRATE_DB_USER`    | CrateDB Username        |
| `CRATE_DB_PASS`    | CrateDB Password        |
| `CRATE_BACKOFF_FACTOR`   | The time between the retries to connect crate is controlled by `CRATE_BACKOFF_FACTOR`. Default value is `0.0` |
| `DEFAULT_LIMIT`    | Max number of rows a query can retrieve |
| `KEEP_RAW_ENTITY`  | Whether to store original entity data |
| `INSERT_MAX_SIZE`  | Maximum amount of data a SQL (bulk) insert should take |
| `POSTGRES_HOST`    | PostgreSQL Host         |
| `POSTGRES_PORT`    | PostgreSQL Port         |
| `POSTGRES_DB_NAME` | PostgreSQL default db   |
| `POSTGRES_DB_USER` | PostgreSQL user         |
| `POSTGRES_DB_PASS` | PostgreSQL password     |
| `POSTGRES_USE_SSL` | `t` or `f` enable SSL   |
| `REDIS_HOST`       | Redis Host              |
| `REDIS_PORT`       | Redis Port              |
| `USE_GEOCODING`    | `True` or `False` enable or disable geocoding |
| `CACHE_GEOCODING`  | `True` or `False` enable or disable caching for geocoding |
| `CACHE_QUERIES`    | `True` or `False` enable or disable caching for queries |
| `DEFAULT_CACHE_TTL`| Time to live of metadata cache, default: 60 (seconds) |                              |
| `QL_CONFIG`        | Pathname for tenant  configuration  |
| `QL_DEFAULT_DB`    | Default backend: `timescale` or `crate`  |
| `CRATE_WAIT_ACTIVE_SHARDS` | Specifies the number of shard copies that need to be active for write operations to proceed. Default `1`. See related [crate documentation](https://crate.io/docs/crate/reference/en/4.3/sql/statements/create-table.html#write-wait-for-active-shards). |
| `USE_FLASK`        | `True` or `False` to use flask server (only for Dev) or gunicorn. Default to `False`  |
| `LOGLEVEL`         | Define the log level for all services (`DEBUG`, `INFO`, `WARNING` , `ERROR`)      |
| `WORKERS`          | Define the number of gunicorn worker processes for handling requests. Default to `2` |
| `THREADS`          | Define the number of gunicorn threads per worker.  Default to `1` **see notes**.  |
| `WQ_OFFLOAD_WORK`  | Whether to offload insert tasks to a work queue. Default: `False`.  |
| `WQ_RECOVER_FROM_ENQUEUEING_FAILURE`  | Whether to run tasks immediately if a work queue isn't available. Default: `False`. |
| `WQ_MAX_RETRIES`   | How many times work queue processors should retry failed tasks. Default: 0 (no retries). |
| `WQ_FAILURE_TTL`   | How long, in seconds, before removing failed tasks from the work queue. Default: 604800 (a week). |
| `WQ_SUCCESS_TTL`   | How long, in seconds, before removing successfully run tasks from the work queue. Default: 86400 (a day). |
| `WQ_WORKERS`       | How many worker queue processors to spawn. |

### Notes

- `DEFAULT_LIMIT`. This variable specifies the upper limit L of rows a query
  operation is allowed to fetch from the database and return to client. The
  actual number of rows will be the least of L and the client-specified limit
  or L if the client didn't specify a limit. If not set through this variable,
  L defaults to 10,000. This variable is read in on each API call to query
  endpoints so it can be set dynamically and it will affect every subsequent
  query operation. The variable string value you set should be convertible to
  an integer, if not, the default value of 10,000 will be used instead.

- `KEEP_RAW_ENTITY`. If true, then each notified entity will be stored in its
  entirety as JSON in an additional column of the corresponding entity table.
  (This may result in the table needing up to 10x more storage.) If false, the
  JSON will only be stored (as detailed earlier) in case the conversion from
  JSON to tabular fails---typically this happens when the notified entity
  contains a previously notified attribute whose type is now different than
  it used to be in the past. This variable is read in on each API call to the
  notify endpoint so it can be set dynamically and it will affect every
  subsequent insert operation. Any of the following (case insensitive) values
  will be interpreted as true: 'true', 'yes', '1', 't', 'y'. Anything else
  counts for false, which is also the default value if the variable is not set.
  
- `THREADS`. Current implementation of ConnectionManager is not thread safe,
  so keep this value to 1.

- `INSERT_MAX_SIZE`. If set, this variable limits the amount of data that
  can be packed in a single SQL bulk insert to the specified value `M`. If
  the size of the data to be inserted exceeds `M`, the data is split into
  smaller batches, each having a size no greater than `M`, and each batch
  is inserted separately, i.e. a separate SQL bulk insert statement is issued
  for each batch. Limiting the amount of data that can be inserted at once
  is useful with some backends like Crate that abort insert operations when
  the data size exceeds an internal threshold. This variable is read in on
  each API call to the notify endpoint so it can be set dynamically and it
  will affect every subsequent insert operation. Accepted values are sizes
  in bytes (B) or `2^10` multiples (KiB, MiB, GiB), e.g. `10 B`, `1.2 KiB`,
  `0.9 GiB`. If this variable is not set (or the set value isn't valid),
  SQL inserts are processed normally without splitting data into batches.

- `WQ_OFFLOAD_WORK`. The notify endpoint supports offloading the insert of
  the received NGSI entities to separate work queue processes. Set this
  variable to true to make QuantumLeap add the entities to a queue within
  the Redis cache instead of inserting them directly into the DB backend,
  which is what would happen if this variable weren't set or set to false.
  (Note that when offloading insert tasks to a work queue, for entities to
  actually be inserted in the DB backend, you will also have to have at
  least one QuantumLeap process configured as a work queue processor.)
  Any of the following (case insensitive) values will be interpreted as
  true: 'true', 'yes', '1', 't', 'y'. Anything else counts for false, which
  is also the default value if the variable is not set.

- `WQ_RECOVER_FROM_ENQUEUEING_FAILURE`. Use this variable to specify what
  to do if the notify endpoint is configured to offload insert tasks to
  a work queue (`WQ_OFFLOAD_WORK=true`) but the enqueueing of an insert
  task fails---typically this can happen when the Redis cache is temporarily
  unavailable. If this variable is set to true, then QuantumLeap attempts
  to recover from this situation by inserting the notify payload directly
  in the DB backend, as if `WQ_OFFLOAD_WORK` were set to false. On the
  other hand, if this variable is set to false or isn't set at all, then
  QuantumLeap will return a server error. Notice that this variable is only
  taken into account if `WQ_OFFLOAD_WORK=true`---if false, then inserts
  are always executed synchronously within the notify endpoint.
  Any of the following (case insensitive) values will be interpreted as
  true: 'true', 'yes', '1', 't', 'y'. Anything else counts for false, which
  is also the default value if the variable is not set.

- `WQ_MAX_RETRIES`. When offloading insert tasks to a work queue, it is
  possible to retry failed insert tasks. Regardless of the value of this
  variable, the first time a task is fetched from the work queue, it is
  run once. If this initial run fails and `WQ_MAX_RETRIES` is set to an
  integer `M > 0`, then the task enters a retry cycle with up to `M` DB
  insert attempts spaced out by an exponentially growing number of seconds.
  (Task execution won't be attempted further if `M <= 0` or `WQ_MAX_RETRIES`
  isn't set or it is set but its value can't be parsed as an integer.)
  The retry cycle works as follows. Consider the growing sequence of positive
  integers `S = { 20 * 2^k | k ∈ ℕ } = (20, 40, 80, 160, 320,...)`, interpret
  them as seconds, call `t0` the time at which the first run failed, consider
  the series `t0 + Σs[k] = (t0 + 20, t0 + 20 + 40, t0 + 20 + 40 + 80,...)`
  and take the first `M` terms `t1 = t0 + 20,..., tM = t0 +...+ s[M]`.
  Now schedule `M` task execution attempts at time points `t1,..., tM`.
  On retrying task execution at time point `t[k]`, if the DB insert succeeds,
  cancel any subsequent scheduled retries and flag the task as successful.
  If the insert fails, what happens next depends on whether the failure is
  transient or permanent. A transient failure is a situation where the task
  may succeed if retried at some time in the future (e.g. a DB connection
  goes down) whereas a permanent failure is a situation where the insert will
  always fail because of a structural error---e.g. a mismatch between an NGSI
  attribute type and its corresponding DB type. In the case of a permanent
  failure, cancel any subsequent scheduled retries and flag the task as
  failed. On the other hand, if the failure is transient, go on with the
  next step of the retry cycle and attempt the task again at time point
  `t[k+1]`. Irrespective of success or failure, if the `M`th attempt is
  reached, the retry cycle ends then.

- `WQ_FAILURE_TTL`. When using a work queue to process notify endpoint
  payloads, the NGSI entities making up the payload will be kept in the
  Redis cache for a period of time so that data can be inspected after
  the insert task has run. More accurately, data are kept in Redis for
  a number of seconds `ttl` past task completion. Regardless of outcome,
  a task is considered complete when it has finished running if no retries
  have been configured or when it has exited the retry cycle in the case of
  retries. Let `t0` be the task completion time. Task data is kept in Redis
  until `t0 + ttl`, past which point it will be automatically removed from
  the Redis cache.
  Use this variable to specify how long failed task data should be kept around
  after the insert task completed with a failure. That is, use this variable
  to specify the above `ttl` in seconds. The default value of `604800` seconds
  (a week) will be used if this variable isn't set or it is set but its value
  can't be parsed as an integer.

- `WQ_SUCCESS_TTL`. This setting is analogous to `WQ_FAILURE_TTL`. Use this
  variable to specify how long, in seconds, data of successful insert tasks
  should be kept around. The default value of `86400` seconds (a day) will
  be used if this variable isn't set or it is set but its value can't be
  parsed as an integer.

- `WQ_WORKERS`. When using a work queue to process notify endpoint payloads,
  you have to start one or more QuantumLeap work queue backends to service
  the work queue where notify payloads are queued for processing. Each
  QuantumLeap backend will fork a number of worker processes to service the
  queue equal to the value of the `WQ_WORKERS` environment variable. To
  start a QuantumLeap work queue backend you have to override the default
  Docker image command with the following:
  `supervisord -n -c ./wq/supervisord.conf`. This command requires that
  `WQ_WORKERS` be set to a positive integer. For example if you set
  `WQ_WORKERS=2`, two worker processes will be started to fetch notification
  payloads from the queue and insert them in the database. These processes
  are managed by [Supervisor][supervisor] and will be automatically restarted
  if they crash.
  
- `CRATE_BACKOFF_FACTOR`. The time between the cratedb connection retries is
  defined by `CRATE_BACKOFF_FACTOR`. The Maximum value of `CRATE_BACKOFF_FACTOR`
  is: `120`. The default value is `0.0`.

- `CRATE_DB_USER`. Only needed if password authentication is used at the Crate
  database. Please ensure the specified user has cluster wide `DML`, `DDL` and
  `DQL` permissions. Example user creation in CrateDB: `CREATE USER quantumleap
  WITH (password = 'a_secret_password'); GRANT DML,DDL,DQL TO quantumleap;`. For
  details please refer to to corresponding Crate documentation ([Authentication
  methods](https://crate.io/docs/crate/reference/en/4.6/admin/auth/methods.html)
  and [Privileges](https://crate.io/docs/crate/reference/en/4.6/admin/privileges.html)).

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

- `QL_CONFIG`: absolute pathname of the QuantumLeap YAML configuration
  file. If not set, the default configuration will be used where only
  the Crate back end is available.

The YAML configuration file specifies what back end to use for which
tenant as well as the default back end to use for any other tenant
not explicitly mentioned in the file. Here's an example YAML
configuration:

```yaml
tenants:
    t1:
        backend: Timescale
    t2:
        backend: Crate
    t3:
        backend: Timescale

default-backend: Crate
```

With this configuration, any NGSI entity coming in for tenant `t1`
or `t3` will be stored in Timescale whereas tenant `t2` will use
Crate. Any tenant other than `t1`, `t2`, or `t3` gets the default
Crate back end.

[crate]: ./crate.md
    "QuantumLeap Crate"
[supervisor]: http://supervisord.org/
    "Supervisor: A Process Control System"
[timescale]: ./timescale.md
    "QuantumLeap Timescale"
