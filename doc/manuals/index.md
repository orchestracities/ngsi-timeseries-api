# QuantumLeap

QuantumLeap is an API that supports the storage of NGSI [FIWARE NGSIv2](http://docs.orioncontextbroker.apiary.io/#) data into a [time series database](https://en.wikipedia.org/wiki/Time_series_database).

In the end, its goals are similar to those of [FIWARE's Comet STH](https://fiware-sth-comet.readthedocs.io/en/latest/
). However, Comet does not yet support NGSIv2, it's tied to MongoDB, and some of the conditions and constraints under which it was developed are no longer hold. That being said, there is nothing wrong with it; this is just an exploration on a new way to provide historical data for FIWARE NGSIv2 with different timeseries databases as backend.

The idea is to keep the translator phase swapable so as to look forward to having support for different timeseries databases. We started testing [InfluxDB](https://docs.influxdata.com/influxdb/), [RethinkDB](https://www.rethinkdb.com/docs/) and [Crate](http://www.crate.io). However, we have decided for now to focus on the NGSIv2-CrateDB translator because we find in [Crate](http://www.crate.io) the following advantages:

- Easy scalability with containerized database cluster out of the box
- Geo-queries support out of the box
- Nice SQL-like querying language to work with
- Supported integration with visualization tools like [Grafana](http://www.grafana.com)


## Typical Usage and How it works

The typical usage scenario for QuantumLeap would be the following:

![Alt text](http://www.gravizo.com/svg?%23%20Convert%20the%20following%20to%20png%20using%20http://www.gravizo.com/%23converter.;@startuml;skinparam%20componentStyle%20uml2;!define%20ICONURL%20https://raw.githubusercontent.com/smartsdk/architecture-diagrams/master/dist;!includeurl%20ICONURL/common.puml;!includeurl%20ICONURL/fiware.puml;!includeurl%20ICONURL/smartsdk.puml;interface%20NGSI;FIWARE%28cb,%22Orion%20\nContext%20Broker%22,component%29;package%20%22IoT%20Layer%22%20{;%20%20%20%20FIWARE%28iota,%22IoT%20Agent%22,component%29;};iota%20-up-%20NGSI;[Client]%20-left-%20NGSI;NGSI%20-up-%20cb;[Client]%20%221%22%20-up-%3E%20cb;iota%20-up-%3E%20%222%22%20cb;package%20%22QuantumLeap%22%20{;SMARTSDK%28api,%22API%22,component%29;SMARTSDK%28reporter,%22Reporter%22,component%29;SMARTSDK%28translator,%22Translator%22,component%29;api%20-up-%20NGSI;%20%20%20%20cb%20%223%22%20-down-%3E%20api;api%20%3C-down-%3E%20translator;api%20-down-%3E%20reporter;reporter%20-right-%3E%20translator;%20%20%20%20[Client]%20%224%22%20%3C-down-%3E%20api;};[DB%20Cluster]%20%3C-left-%20translator;[Grafana]%20%3C-down-%20[DB%20Cluster];[Client]%20%225%22%20%3C-down-%20[Grafana];@enduml;)

The idea of **QuantumLeap** is pretty straightforward. By leveraging on the [notifications mechanism](http://fiware-orion.readthedocs.io/en/latest/user/walkthrough_apiv2/index.html#subscriptions), clients instruct Orion **(1)** to notify QuantumLeap of the changes in the entities they care about. Details of this process are explained in the [Orion Subscription part of the User Manual](user/index.md#orion-subscription).

There is typically a whole **IoT layer** governed by 1 or more [IoT Agents](https://catalogue.fiware.org/enablers/backend-device-management-idas) pushing data in NGSI format to the **[Orion Context Broker](https://fiware-orion.readthedocs.io
)** **(2)**.

Notifications will arrive to QuantumLeap's API `/v2/notify` endpoint **(3)**. Its **Reporter** submodule will parse and validate the notification and eventually feed it to the configured **Translator**. The Translator is ultimately the responsible for persisting the NGSI information to the configured times-series database cluster.

In addition to the `/v2/notify` endpoint, the API is planned to include NGSI endpoints for advanced raw and aggregated data retrieval **(4)** for clients to query historical data.

For the visualisation of data **(5)** at the time being we are experimenting with [Grafana](http://grafana.com/) complemented with open source plugins for the databases. In the future, we could envision a plugin for direct interaction with the *query* API.

### More information

- Refer to the [Admin Guide](admin/index.md) for info on how to install QuantumLeap and get it running.
- Refer to the [User Manual](user/index.md) for more info on how to use it.
