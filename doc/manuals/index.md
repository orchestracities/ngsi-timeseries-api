# QuantumLeap

QuantumLeap is an adapter aimed to bring [FIWARE NGSIv2](http://docs.orioncontextbroker.apiary.io/#) Historical Data on top of TimeSeries Databases.

In the end, its goals are similar to those of [FIWARE's Comet STH](https://fiware-sth-comet.readthedocs.io/en/latest/
). However, Comet does not yet support NGSIv2, it's tied to MongoDB, and some of the conditions and constraints under which it was developed are no longer hold. That being said, there is nothing wrong with it; this is just an exploration on a new way to provide historical data for FIWARE NGSIv2 with different timeseries databases as backend.

The idea is to keep the translator phase swapable so as to look forward to having support for different timeseries databases. We started testing [InfluxDB](https://docs.influxdata.com/influxdb/), [RethinkDB](https://www.rethinkdb.com/docs/) and [Crate](http://www.crate.io). However, we have decided for now to focus on the NGSIv2-CrateDB translator because we find in [Crate](http://www.crate.io) the following advantages:

- Easy scalability with containerized database cluster out of the box
- Geo-queries support out of the box
- Nice SQL-like querying language to work with
- Supported integration with visualization tools like [Grafana](http://www.grafana.com)


## Typical Usage and How it works

The typical usage scenario for QuantumLeap would be the following:

![Alt text](https://g.gravizo.com/svg?@startuml;skinparam%20componentStyle%20uml2;!define%20ICONURL%20https://raw.githubusercontent.com/smartsdk/architecture-diagrams/master/dist;!includeurl%20ICONURL/common.puml;!includeurl%20ICONURL/fiware.puml;!includeurl%20ICONURL/smartsdk.puml;interface%20NGSI;FIWARE%28cb,%22Context%20Broker%20\n%20-%20Orion%22,component%29;[Sensor%20@%20IoT%20Layer]%20-right-%20NGSI;NGSI%20-right-%20cb;package%20%22QuantumLeap%22%20{;SMARTSDK%28api,%22API%22,component%29;SMARTSDK%28reporter,%22Reporter%22,component%29;SMARTSDK%28translator,%22Translator%22,component%29;api%20-up-%20NGSI;api%20%3C-down-%3E%20translator;api%20%22/notify%22%20-down-%3E%20reporter;reporter%20-right-%3E%20translator;};[CrateDB]%20%3C-left-%20translator;[Grafana]%20-down-%20CrateDB;@enduml;)

To begin with, you have an **IoT layer** pushing data in NGSI format to the **[Orion Context Broker](https://fiware-orion.readthedocs.io
)**.

The idea of **QuantumLeap** is pretty straightforward. By leveraging on the [notifications mechanism](http://fiware-orion.readthedocs.io/en/latest/user/walkthrough_apiv2/index.html#subscriptions), you instruct Orion to notify QuantumLeap of the changes in the entities you care about. Details of this process are explained in [this section](user/ngsi_notification.md). Notifications will arrive to QuantumLeap's API *'/notify'* endpoint. Its **Reporter** submodule will parse and validate the notification and eventually feed it to the configured **Translator**. The Translator is ultimately responsible for persisting the NGSI information to the configured times-series database.

In addition to the *'/notify'* endpoint, the API is planned to include NGSI endpoints for advanced raw and aggregated data retrieval.


### More information

- Refer to the [Admin Guide](admin/index.md) for info on how to install QuantumLeap and get it running.
- Refer to the [User Manual](user/index.md) for more info on how to use it.
