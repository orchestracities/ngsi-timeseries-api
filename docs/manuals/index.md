# QuantumLeap

[![FIWARE Core Context Management](https://img.shields.io/badge/FIWARE-Core-233c68.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABsAAAAVCAYAAAC33pUlAAAABHNCSVQICAgIfAhkiAAAA8NJREFUSEuVlUtIFlEUx+eO+j3Uz8wSLLJ3pBiBUljRu1WLCAKXbXpQEUFERSQF0aKVFAUVrSJalNXGgmphFEhQiZEIPQwKLbEUK7VvZrRvbr8zzjfNl4/swplz7rn/8z/33HtmRhn/MWzbXmloHVeG0a+VSmAXorXS+oehVD9+0zDN9mgk8n0sWtYnHo5tT9daH4BsM+THQC8naK02jCZ83/HlKaVSzBey1sm8BP9nnUpdjOfl/Qyzj5ust6cnO5FItJLoJqB6yJ4QuNcjVOohegpihshS4F6S7DTVVlNtFFxzNBa7kcaEwUGcbVnH8xOJD67WG9n1NILuKtOsQG9FngOc+lciic1iQ8uQGhJ1kVAKKXUs60RoQ5km93IfaREvuoFj7PZsy9rGXE9G/NhBsDOJ63Acp1J82eFU7OIVO1OxWGwpSU5hb0GqfMydMHYSdiMVnncNY5Vy3VbwRUEydvEaRxmAOSSqJMlJISTxS9YWTYLcg3B253xsPkc5lXk3XLlwrPLuDPKDqDIutzYaj3eweMkPeCCahO3+fEIF8SfLtg/5oI3Mh0ylKM4YRBaYzuBgPuRnBYD3mmhA1X5Aka8NKl4nNz7BaKTzSgsLCzWbvyo4eK9r15WwLKRAmmCXXDoA1kaG2F4jWFbgkxUnlcrB/xj5iHxFPiBN4JekY4nZ6ccOiQ87hgwhe+TOdogT1nfpgEDTvYAucIwHxBfNyhpGrR+F8x00WD33VCNTOr/Wd+9C51Ben7S0ZJUq3qZJ2OkZz+cL87ZfWuePlwRcHZjeUMxFwTrJZAJfSvyWZc1VgORTY8rBcubetdiOk+CO+jPOcCRTF+oZ0okUIyuQeSNL/lPrulg8flhmJHmE2gBpE9xrJNkwpN4rQIIyujGoELCQz8ggG38iGzjKkXufJ2Klun1iu65bnJub2yut3xbEK3UvsDEInCmvA6YjMeE1bCn8F9JBe1eAnS2JksmkIlEDfi8R46kkEkMWdqOv+AvS9rcp2bvk8OAESvgox7h4aWNMLd32jSMLvuwDAwORSE7Oe3ZRKrFwvYGrPOBJ2nZ20Op/mqKNzgraOTPt6Bnx5citUINIczX/jUw3xGL2+ia8KAvsvp0ePoL5hXkXO5YvQYSFAiqcJX8E/gyX8QUvv8eh9XUq3h7mE9tLJoNKqnhHXmCO+dtJ4ybSkH1jc9XRaHTMz1tATBe2UEkeAdKu/zWIkUbZxD+veLxEQhhUFmbnvOezsJrk+zmqMo6vIL2OXzPvQ8v7dgtpoQnkF/LP8Ruu9zXdJHg4igAAAABJRU5ErkJgggA=)](https://www.fiware.org/developers/catalogue/)
[![](https://img.shields.io/badge/tag-fiware-orange.svg?logo=stackoverflow)](https://stackoverflow.com/questions/tagged/fiware)

## Overview

QuantumLeap is the first implementation of an API that supports the storage of
NGSI [FIWARE NGSIv2](http://docs.orioncontextbroker.apiary.io/#) data into a
[time-series database](https://en.wikipedia.org/wiki/Time_series_database),
known as [ngsi-tsdb](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb).

In the end, it has similar goals to those of [FIWARE's STH Comet](https://fiware-sth-comet.readthedocs.io/en/latest/).
However, Comet does not yet support NGSIv2, it's strongly tied to MongoDB, and
some of the conditions and constraints under which it was developed are no
longer hold. That being said, there is nothing wrong with it; this is just an
exploration on a new way to provide historical data for FIWARE NGSIv2 with
different time-series databases as backend.

The idea is to keep the time-series database swappable so as to look forward to
having support for different ones. We started testing
[InfluxDB](https://docs.influxdata.com/influxdb/), [RethinkDB](https://www.rethinkdb.com/docs/)
and [CrateDB](http://www.crate.io). However, we have decided for now to focus the
development on the translator for [CrateDB](http://www.crate.io) because of the
following advantages:

- Easy scalability with [containerised database cluster](https://crate.io/docs/crate/guide/en/latest/deployment/containers/index.html)
out of the box.
- [Geo-queries](https://crate.io/docs/crate/reference/en/latest/general/dql/geo.html)
support out of the box
- Nice [SQL-like querying language](https://crate.io/docs/crate/reference/en/latest/sql/index.html)
to work with
- [Supported integration](https://grafana.com/plugins/crate-datasource/installation)
with visualisation tools like [Grafana](http://www.grafana.com)

## Typical Usage and How it works

The typical usage scenario for QuantumLeap would be the following (notice the
numbering of the events)...

![QL Architecture](rsrc/architecture.png)

The idea of **QuantumLeap** is pretty straightforward. By leveraging on the [NGSIv2 notifications mechanism](http://fiware-orion.readthedocs.io/en/latest/user/walkthrough_apiv2/index.html#subscriptions),
clients first create an Orion subscription **(1)** to notify QuantumLeap of the
changes in the entities they care about. This can be done either through
*QuantumLeap*'s API or directly talking to *Orion*. Details of this process are
explained in the [Orion Subscription part of the User Manual](user/index.md#orion-subscription).

Then, new values arrive in [Orion Context Broker](https://fiware-orion.readthedocs.io)
**(2)** for the entities of interest, for example from a whole **IoT layer**
governed by 1 or more [IoT Agents](https://catalogue.fiware.org/enablers/backend-device-management-idas)
pushing data in NGSI format. Consequently, notifications will arrive to
QuantumLeap's API [/v2/notify](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb)
endpoint **(3)**.

QuantumLeap's **Reporter** submodule will parse and validate the received
notification and eventually feed it to the configured **Translator**. The
Translator is ultimately responsible for persisting the NGSI information to the
configured times-series database cluster.

The current API includes some endpoints for raw and aggregated data retrieval
**(4)** for clients to query historical data. It also supports deletion of
historical records. Please note not all endpoints are currently implemented in
QL. For more info about the API, you can refer to the
[NGSI-TSDB specification](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb).

For the visualisation of data **(5)**, at the time being we are using
[Grafana](http://grafana.com/), complemented with open source plugins for the
databases. In the future, we could envision a grafana plugin for direct
interaction with QL's API.

## More information

- Refer to the [Admin Guide](admin/index.md) to learn more about installing
QuantumLeap and getting it running.
- Refer to the [User Manual](user/index.md) to learn more about how to use it
and connect it to other complementary services.
- Have a look at the [SmartSDK guided tour](http://guided-tour-smartsdk.readthedocs.io/en/latest/)
for more examples of QuantumLeap usage.
