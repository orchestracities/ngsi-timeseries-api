# CrateDB

[**CrateDB**](https://crate.io) is QuantumLeap's default backend where NGSI data
will be persisted. In addition to using QL's API, if you want to by-pass QL, you
can also interact directly with CrateDB to query all the data QuantumLeap has
stored from the received notifications. This of course is not recommended as
your implementation will depend on QL implementation details that may change in
future.

CrateDB is a simple to use database backend for many applications. Nowadays a
huge percentage of data is geo-tagged already.
CrateDB can be used to store and query geographical information of many kinds
using the [geo_point](https://crate.io/docs/crate/reference/en/latest/general/ddl/data-types.html#geo-point-data-type)
and [geo_shape](https://crate.io/docs/crate/reference/en/latest/general/ddl/data-types.html#geo-shape-data-type)
types.
With these it is possible to store geographical locations,ways, shapes, areas
and other entities. These can be queried for distance, containment, intersection
and so on.
Currently, CrateDB supports 2D coordinates but it does [not supports 3D coordinate](https://tools.ietf.org/html/rfc7946#section-3.1)

If you followed the [Installation Guide](./installing.md), you have a ready-to-use
CrateDB instance running in a Docker container. The easiest way to interact with
it is using its admin interface, as documented [here](https://crate.io/docs/clients/admin-ui/en/latest/).
Alternatively, you can use its [HTTP api](https://crate.io/docs/crate/getting-started/en/latest/first-use/query.html#the-cratedb-http-endpoint),
or any of its [supported clients](https://crate.io/docs/crate/tutorials/en/latest/getting-started/start-building/index.html).

**Note**- Crate(3.x and 4.x) does not support nested arrays.

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

You can learn more about CrateDB by reading [the docs](https://crate.io/docs/crate/reference/).
