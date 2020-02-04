# CrateDB

[**CrateDB**](https://crate.io) is QuantumLeap's default backend where NGSI data
will be persisted. In addition to using QL's API, if you want to by-pass QL, you
can also interact directly with CrateDB to query all the data QuantumLeap has
stored from the received notifications. This of course is not recommended as
your implementation will depend on QL implementation details that may change in
future.

If you followed the [Installation Guide](./index.md), you have a ready-to-use
CrateDB instance running in a Docker container. The easiest way to interact with
it is using its admin interface, as documented [here](https://crate.io/docs/clients/admin-ui/en/latest/).
Alternatively, you can use its [HTTP api](https://crate.io/docs/crate/getting-started/en/latest/first-use/query.html#the-cratedb-http-endpoint),
or any of its [supported clients](https://crate.io/docs/crate/tutorials/en/latest/getting-started/start-building/index.html).

You can learn more about CrateDB by reading [the docs](https://crate.io/docs/crate/reference/).
