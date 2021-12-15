# CrateDB

[**CrateDB**](https://crate.io) is QuantumLeap's default backend where NGSI data
will be persisted. In addition to using QuantumLeap's API, if you want to
by-pass QuantumLeap, you can also interact directly with CrateDB to query all
the data QuantumLeap has stored from the received notifications.
This of course is not recommended as your implementation will depend
on QuantumLeap implementation details that may change in future.

CrateDB is a simple to use database backend for many applications. Nowadays a
huge percentage of data is geo-tagged already.
CrateDB can be used to store and query geographical information of many kinds
using the [geo_point](https://crate.io/docs/crate/reference/en/latest/general/ddl/data-types.html#geo-point-data-type)
and [geo_shape](https://crate.io/docs/crate/reference/en/latest/general/ddl/data-types.html#geo-shape-data-type)
types.
With these it is possible to store geographical locations, ways, shapes, areas
and other entities. These can be queried for distance, containment, intersection
and so on.
Currently, CrateDB supports 2D coordinates but it does [not supports 3D coordinate](https://tools.ietf.org/html/rfc7946#section-3.1)

If you followed the [Installation Guide](./installing.md), you have a ready-to-use
CrateDB instance running in a Docker container. The easiest way to interact with
it is using its admin interface, as documented [here](https://crate.io/docs/clients/admin-ui/en/latest/).
Alternatively, you can use its [HTTP api](https://crate.io/docs/crate/getting-started/en/latest/first-use/query.html#the-cratedb-http-endpoint),
or any of its [supported clients](https://crate.io/docs/crate/tutorials/en/latest/getting-started/start-building/index.html).

You can learn more about CrateDB by reading [the docs](https://crate.io/docs/crate/reference/).
