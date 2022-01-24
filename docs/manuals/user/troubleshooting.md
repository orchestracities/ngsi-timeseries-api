# Troubleshooting

Something not working as expected? Don't worry! the expected thing is for it
not to work :p.

Checkout the following section to make sure you didn't miss a critical step,
and if none of that applies to your case, then proceed to the **Bug reporting**.

## FAQs

### Followed the instructions, but nothing happens

If you don't see your data being saved in the database, before reporting a bug
please ask yourself the following questions:

- Have you created a subscription for the entity type you are inserting? Is
the subscription NGSIv2 and WITHOUT the "keyValues" option?. Review the
[Orion Subscriptions Docs](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#subscriptions).

- Are you inserting/updating attributes listed in the "condition" of the
subscription? I.e, will Orion trigger notifications for that insert/update?

- Can you see such subscription if you query Orion subscriptions? When is its
"last_success"?

- Is the location of QuantumLeap expressed in the *notify_url* field of the
subscription a resolvable url for the containerised Orion? Review the
[Usage Section](./using.md) for more details.

- Are you running the different components behind firewalls? If so, did you
open the corresponding ports? (See the [Ports](../admin/ports.md) section.)

### Cannot retrieve data

- Are you using the correct FIWARE headers for the tenant? Refer to the [Multi-tenancy](using.md#multi-tenancy)
part of the docs.

- Is the endpoint you are using implemented? Note for now some of them are not.
These are flagged in the API specification.

- Have a look at the message in the returned body for hints of what could have
gone wrong. You may be missing an important parameter in your request.

### I got no errors but I cannot see data in my Dashboards

Make sure you have enough data points in your database and that your selection
of time slice (on the top-right corner of grafana) is actually covering a time
range in which you have data.

### 3D Coordinates are not working when using CrateDB as backend

If you spot an error such as:

```bash
crate.client.exceptions.ProgrammingError: SQLActionException[ColumnValidationException: Validation failed for location: Cannot cast {"coordinates"=[51.716783624, 8.752131611, 23], "type"='Point'} to type geo_shape]
```

This related to the fact that CrateDB does not support 3D coordinates,
as documented in [admin documentation](../admin/crate.md).

### Crate(3.x and 4.x) does not support nested arrays

When a table is created with two columns `x` and `y` of type object
and array(object).
Inserting an object in x and y gives a below exception message:

```#!/bin/bash
create table t (x object, y array(object));
insert into t (x) values ('{ "x": [1] }');
  - ok
insert into t (x) values ('{ "x": [[1, 2], [3, 4]] }');
  - SQLActionException[ColumnValidationException: Validation failed for x:
  -Cannot cast '{ "x": [[1, 2], [3, 4]] }' to type object]
insert into t (y) values (['{ "x": [[1, 2], [3, 4]] }']);
  -SQLActionException[ElasticsearchParseException:nested arrays not supported]
```

### Sometimes it takes more than 500 msec to read the data sent to Orion in QuantumLeap

QuantumLeap is a Timeseries API that stores values forwarded by the Context Broker,
and due to the nature of its backends as well, there is always some synch
latency between the data writing and the time the data is available for reading.

1. Orion takes some msec to process a request and trigger a notification.

1. The QuantumLeap takes some msec to process a single message and store it in
    the database.

1. Especially in the case of CrateDB, indexing of inserted data may take a bit,
    so this means that there is additional latency between when the a message
    is stored in crate, and when it is actually available for querying. In case
    of multi-node CrateDB deployment this can take even more because QuantumLeap
    writes on Crate node A, first the data is indexed in node A, and then
    replicated on node B. So if you issue a query right after writing a message
    and QuantumLeap picks node B, probability to find the data you just pushed
    is even lower.

### Crate configuration and active shards

The `wait_for_active_shards` value only affects table (or partition) creation
and is not (directly) affecting writes.
In case of a partitioned table, new partitions are created on-fly taking this
setting into account and such this setting will partly affect writes here.
If not all defined N shards for this new partition are active, the write will
stall until the replica becomes active or an internal timeout of `30s` is
reached. Thus writes get slow if e.g. the setting is set to > `1` and replica
shards are unassigned/unreachable due to a missing node.

To avoid such slow writes (and possible data loss due to missing replicas )
when `write_for_active_shards` is set to `>1` while doing a
[rolling upgrade](https://crate.io/docs/crate/howtos/en/latest/admin/rolling-upgrade.html),
`cluster.graceful_stop.min_availability` should be set to `full` and nodes must
be shutdown gracefully . By doing so, it is ensured that primary **and**
replica shards are moved away from the to-shutdown node **before** the
node will stop.

Here's the scenario:

1. A node N1 holds a primary shard S with records r[1] to r[m + n].
1. Another node N2 holds S's replica shard, R, with records r[1] to r[m],
    i.e. n records haven't been replicated yet.
1. N1 goes down.
1. Crate won't promote N2 as primary since it knows R is stale w/r/t S.

The only way out of the impasse would be to manually force replica promotion.

In case N1 goes down **before**  the operation request was sent on the replica
shard at N2, the cluster will not promote the (stale) replica as a new primary
and thus won't process any new writes, resulting in a red table health.
After the primary shard comes back (yellow/green health, writes possible again),
the missing operations are synced to the replica.
If the primary cannot be started (e.g. due to disk corruption) the replica
can be [forced](https://crate.io/docs/crate/reference/en/4.3/sql/statements/alter-table.html#alter-table-reroute-promote-replica)
to be promoted as the new primary. Of course the missing operations
are then lost.

If N1 goes down **after** the replication request was sent, the replica may
process the operation and afterwards can be promoted as a new primary.

See also [storage-consistency](https://crate.io/docs/crate/reference/en/4.3/concepts/storage-consistency.html),
[resiliency](https://crate.io/docs/crate/reference/en/4.3/concepts/resiliency.html)
and [resiliency](https://crate.io/docs/crate/reference/en/4.3/appendices/resiliency.html).

## Bug reporting

Bugs should be reported in the form of
[issues](https://github.com/orchestracities/ngsi-timeseries-api/issues)
in the github repository.

Please, look through the open issues before opening a duplicated one :)

Include as much context info as possible, also ideally the following things:

- The inserted entity that may have caused the problem. E.g:

```json
{
    'id': 'MyEntityId',
    'type': 'MyEntityType',
    'attr1': 'blabla',
    ...
}
```

- The payload of the subscription(s) that you created. See [this section](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#subscriptions)
of Orion documentation.

- The logs of the QuantumLeap container.

    The logs can be retrieved with the [docker logs command](https://docs.docker.com/engine/reference/commandline/logs/#options)
    or [docker service logs](https://docs.docker.com/engine/reference/commandline/service_logs/)
    if you deployed QuantumLeap as a service. In the first case, you can
    discover the container id with `docker ps -a`. In the second case, use
    `docker service ls` to find the service name.
