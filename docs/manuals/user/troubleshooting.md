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


#### CrateDB Datasource is not available in Grafana.

By default, QuantumLeap recipes deploy Grafana with crate's plugin already
installed. See []().

If you don't see crate as an option while creating the datasource as explained
in [Grafana section](../admin/grafana.md), either the grafana container failed
to get internet connectivity (to download and install the plugin) or you are
using an external grafana instance that needs to get the plugin installed.

Go [here]() for documentation on crate's datasource plugin or
[here](http://docs.grafana.org/plugins/installation/) for documentation on
installing grafana plugins in general.

## Bug reporting

Bugs should be reported in the form of
[issues](https://github.com/smartsdk/ngsi-timeseries-api/issues) in the github
repository.

Please, look through the open issues before opening a repeated one :)

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
