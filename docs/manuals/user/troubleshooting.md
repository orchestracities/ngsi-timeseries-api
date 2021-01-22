# Troubleshooting

Something not working as expected? Don't worry! the expected thing is for it
not to work :p.

Checkout the following section to make sure you didn't miss a critical step,
and if none of that applies to your case, then proceed to the **Bug reporting**.

## FAQs

#### Followed the instructions, but nothing happens

If you don't see your data being saved in the database, before reporting a bug
please ask yourself the following questions:

- Have you created a subscription for the entity type you are inserting? Is
the subscription NGSIv2 and WITHOUT the "keyValues" option?. Review the [Orion Subscriptions Docs](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#subscriptions).

- Are you inserting/updating attributes listed in the "condition" of the
subscription? I.e, will Orion trigger notifications for that insert/update?

- Can you see such subscription if you query Orion subscriptions? When is its
"last_success"?

- Is the location of QuantumLeap expressed in the *notify_url* field of the
subscription a resolvable url for the containerised Orion? Review the
[Usage Section](./index.md) for more details.

- Are you running the different components behind firewalls? If so, did you
open the corresponding ports? (See the [Ports](../admin/ports.md) section.)

#### Cannot retrieve data

- Are you using the correct FIWARE headers for the tenant? Refer to the [Multi-tenancy](index.md#multi-tenancy)
part of the docs.

- Is the endpoint you are using implemented? Note for now some of them are not.
These are flagged in the API specification.

- Have a look at the message in the returned body for hints of what could have
gone wrong. You may be missing an important parameter in your request.

#### I got no errors but I cannot see data in my Dashboards

Make sure you have enough data points in your database and that your selection
of time slice (on the top-right corner of grafana) is actually covering a time
range in which you have data.

#### 3D Coordinates are not working when using CrateDB as backend.

If you spot an error such as:
```
crate.client.exceptions.ProgrammingError: SQLActionException[ColumnValidationException: Validation failed for location: Cannot cast {"coordinates"=[51.716783624, 8.752131611, 23], "type"='Point'} to type geo_shape]
```
This related to the fact that CrateDB does not support 3D coordinates,
as documented in [admin documentation](../admin/crate.md).

### Sometimes it takes more than 500 msec to read the data sent to Orion in QuantumLeap
 
QuantumLeap is a Timeseries API that stores values forwarded by the Context Broker,
and due to the nature of its backends as well, there is always some synch
latency between the data writing and the time the data is available for reading.

1. Orion takes some msec to process a request and trigger a notification.

1. The QL takes some msec to process a single message and store it in the database.

1. Especially in the case of CrateDB, indexing of inserted data may take a bit,
    so this means that there is additional latency between when the a message
    is stored in crate, and when it is actually available for querying. In case
    of multi-node CrateDB deployment this can take even more because QL writes
    on Crate node A, first the data is indexed in node A, and then replicated
    on node B. So if you issue a query right after writing a message and QL
    picks node B, probability to find the data you just pushed is even lower.

## Bug reporting

Bugs should be reported in the form of
[issues](https://github.com/smartsdk/ngsi-timeseries-api/issues) in the github
repository.

Please, look through the open issues before opening a duplicated one :)

Include as much context info as possible, also ideally the following things:

- The inserted entity that may have caused the problem. E.g:

        {
            'id': 'MyEntityId',
            'type': 'MyEntityType',
            'attr1': 'blabla',
            ...
        }

- The payload of the subscription(s) that you created. See [this section](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#subscriptions)
of Orion documentation.

- The logs of the QuantumLeap container.

    The logs can be retrieved with the [docker logs command](https://docs.docker.com/engine/reference/commandline/logs/#options)
    or [docker service logs](https://docs.docker.com/engine/reference/commandline/service_logs/)
    if you deployed QL as a service. In the first case, you can discover the
    container id with `docker ps -a`. In the second case, use
    `docker service ls` to find the service name.
