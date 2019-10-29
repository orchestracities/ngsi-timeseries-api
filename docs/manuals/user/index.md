# Using QuantumLeap

First you need to have QuantumLeap and its complementary services running (of
course). Refer to the [Installation Manual](../admin/index.md) for instructions.

Then, you need to connect *Orion Context Broker* to QuantumLeap through an
[NGSIv2 subscription](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#subscriptions)
for each [Entity Type](https://orioncontextbroker.docs.apiary.io/#introduction/specification/terminology)
whose historical data you are interested in.

Not an Orion expert yet? No problem, you can create the subscription through
QuantumLeap's API. However, you will still need to understand the basics of
how subscriptions and notifications work, so take your time to read
[the docs](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#ubscriptions).

Historical data for each entity type will be added in the QuantumLeap's database as long as the subscription is active, correctly configured and the entity in the notification is NGSI compliant.

In case the subscription is removed or its status is changed, no data will be added after that. Although the previous data stored in QuantumLeap's database will persist until it is removed externally using APIs to delete data stored in QuantumLeap.

So, summing up, the usage flow is therefore the following...

- Create an Orion subscription for each entity type of your interest
- Insert/Update your entities in Orion as usual
- Your historical data will be persisted in QuantumLeap's database

Let's take a closer look at each step.

## Orion Subscription

As stated before, the link between Orion and QuantumLeap is established
through a subscription you need to create. It is therefore important that you
understand well how the NGSIv2 Subscription mechanism works. This is carefully
explained in the corresponding section of [Orion docs](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#subscriptions).

To create the subscription, QuantumLeap offers an API endpoint documented
[here at /subscribe](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb).

Alternatively, you can directly talk to Orion and create the subscription as you
prefer. Here's an example of the payload of the subscription you need to create
in Orion to establish the link Orion-QuantumLeap.

```
    {
        "description": "Test subscription",
        "subject": {
            "entities": [
            {
                "idPattern": ".*",
                "type": "Room"
            }
            ],
            "condition": {
                "attrs": [
                "temperature"
                ]
            }
        },
        "notification": {
            "http": {
                "url": "http://quantumleap:8668/v2/notify"
            },
            "attrs": [
            "temperature"
            ],
            "metadata": ["dateCreated", "dateModified"]
        },
        "throttling": 5
    }
```

Important things to notice from the subscription.

- Notifications must come in complete [NGSI JSON Entity Representation](http://docs.orioncontextbroker.apiary.io/#introduction/specification/json-attribute-representation)
 form. Other forms, such as the [simplified entity representation](http://docs.orioncontextbroker.apiary.io/#introduction/specification/simplified-entity-representation)
 are **NOT** supported by QL because they lack information on attribute types,
 required by QL to make proper translations. This means, *DO NOT* use options
 like `"attrsFormat": "keyValues"`

- The `"url"` field of the subscription specifies where Orion will send the
notifications. I.e, this must be QuantumLeap's `/v2/notify` endpoint.
By default, QuantumLeap listens at port `8668`. This url must be resolvable
from Orion's container, so avoid using *localhost* or something that will not
translate either by Docker, your `/etc/hosts` or DNS to the endpoint where
QuantumLeap is running.

- Though not compulsory, it is highly recommended to include the
`"metadata": ["dateCreated", "dateModified"]` part in the `notification`
part of the subscription. This instructs Orion to include the modification time
of the attributes in the notification. This timestamp will be used as the
**time index** in the database if possible. See the *Time Index* section for
more details.

- You can create any valid NGSI subscription for your entities respecting the
previous rules.

## Data Insertion

By now, it should be clear you don't typically insert data directly into
QuantumLeap. You insert into Orion and Orion notifies QuantumLeap.
For inserts and updates in Orion, refer to the [docs](http://fiware-orion.readthedocs.io/en/latest/user/walkthrough_apiv2/index.html#issuing-commands-to-the-broker).

It's not a problem if inserts were done before you created the
subscription. Of course, you will only get historical records of the updates
happening after the subscription was created.

Here's an example of an insert payload to Orion that will generate a
notification to QuantumLeap based on the "Test subscription" example shown
before.

```
{
    "id": "Room1",
    "type": "Room",
    "temperature": {
        "value": 24.2,
        "type": "Number",
        "metadata": {}
    },
    "pressure": {
        "value": 720,
        "type": "Number",
        "metadata": {}
    }
    "colour": {
        "value": "white",
        "type": "Text",
        "metadata": {}
    }
}
```

If you have a custom scenario and still want to directly insert to QuantumLeap,
it is not impossible. However, you will have to use the same payload Orion uses
in the Notification. Also, you will need attention to some other details you
will have to discover on your own. This is not fully documented because it's not
considered a common workflow.

### Attributes DataType Translation

You need to make sure your NGSI entities are using the valid NGSI types for the
attributes, which are documented in the *Specification* section of the [NGSI API](http://telefonicaid.github.io/fiware-orion/api/v2/latest/). See the first
column of the translation table below, and mind its capitalisation.

The table below shows which attribute types will be translated to which
[CrateDB Data Types](https://crate.io/docs/crate/reference/sql/data_types.html).

**CrateDB Translation Table**

| NGSI Type          | CrateDB Type          | Observation |
| ------------------ |:-----------------------:| :-----------|
|Array               | [array(string)](https://crate.io/docs/crate/reference/sql/data_types.html#array)           | [Issue 36: Support arrays of other types](https://github.com/smartsdk/ngsi-timeseries-api/issues/36) |
|Boolean             | [boolean](https://crate.io/docs/crate/reference/sql/data_types.html#boolean)                 | - |
|DateTime            | [timestamp](https://crate.io/docs/crate/reference/sql/data_types.html#timestamp)                 | 'ISO8601' can be used as equivalent of 'DateTime'. |
|Integer             | [long](https://crate.io/docs/crate/reference/sql/data_types.html#numeric-types)                  | - |
|[geo:point](http://docs.orioncontextbroker.apiary.io/#introduction/specification/geospatial-properties-of-entities)            | [geo_point](https://crate.io/docs/crate/reference/sql/data_types.html#geo-point)               | **Attention!** NGSI uses "lat, long" order whereas CrateDB stores points in [long, lat] order.|
|[geo:json](http://docs.orioncontextbroker.apiary.io/#introduction/specification/geospatial-properties-of-entities)            | [geo_shape](https://crate.io/docs/crate/reference/sql/data_types.html#geo-shape)               | - |
|Number              | [float](https://crate.io/docs/crate/reference/sql/data_types.html#numeric-types)                   |-|
|Text                | [string](https://crate.io/docs/crate/reference/sql/data_types.html#string)                  | This is the default type if the provided NGSI Type is unsupported or wrong. |
|StructuredValue     | [object](https://crate.io/docs/crate/reference/sql/data_types.html#object)                  |-|

If the type of any of the received attributes is not present in the column
*NGSI Type* of the previous table, the value of such attribute will be treated
internally as a string. So, if you use `Float` for your attribute type (not
valid), your attribute will be stored as a `string`.

### Time Index

A fundamental element in the time-series database is the **time index**.
You may be wondering... where is it stored? QuantumLeap will persist the
*time index* for each notification in a special column called `time_index`.

The value that is used for the *time index* of a received notification is
defined according to the following policy, which choses the first present and
valid time value chosen from the following ordered list of options.

1. Custom **time index**. The value of the `Fiware-TimeIndex-Attribute` http
header. Note that for a notification to contain such header, the corresponding
subscription has to be created with an `httpCustom` block, as detailed in the
*Subscriptions and Custom Notifications* section of the [NGSI spec](http://fiware.github.io/specifications/ngsiv2/stable/).
This is the way you can instruct QL to use custom attributes of the
notification payload to be taken as *time index* indicators.

1. Custom **time index** metadata. The most recent custom time index (the value of the `Fiware-TimeIndex-Attribute`)
attribute value found in any of the attribute metadata sections in the notification.
See the previous option about the details regarding subscriptions.

1. **TimeInstant** attribute. As specified in the
[FIWARE IoT agent documentation](https://github.com/telefonicaid/iotagent-node-lib#the-timeinstant-element).

1. **TimeInstant** metadata. The most recent `TimeInstant` attribute value
found in any of the attribute metadata sections in the notification.
(Again, refer to the [FIWARE IoT agent documentation](https://github.com/telefonicaid/iotagent-node-lib#the-timeinstant-element).)

1. **timestamp** attribute.

1. **timestamp** metadata. The most recent `timestamp` attribute value found in any of the attribute metadata sections
in the notification. As specified in the
[FIWARE data models documentation](https://fiware-datamodels.readthedocs.io/en/latest/guidelines/index.html#dynamic-attributes).

1. **dateModified** attribute. If you payed attention in the
[Orion Subscription section](#orion-subscription), this is the `"dateModified"`
value notified by Orion.

1. **dateModified** metadata. The most recent dateModified attribute value
found in any of the attribute metadata sections in the notification.

1. Finally, QL will use the **Current Time** (the time of notification
reception) if none of the above options is present or none of the values found
can actually be converted to a `datetime`.

### Restrictions and Limitations

- You cannot have two entity types with the same name but different
capitalisation. E.g: `Preprocessor` and `preProcessor`. The same applies for
attribute names of a given entity. I.e, attributes `hotSpot` and `hotspot`
will be treated as the same. These are rare corner-cases, but it is worth
keeping in mind this. Ultimately, the correct naming of types and attributes
should respect the naming guidelines explained
[here](http://fiware-datamodels.readthedocs.io/en/latest/guidelines/index.html).

- Attributes metadata are still not being persisted. See [Issue 12](https://github.com/smartsdk/ngsi-timeseries-api/issues/12)

- While support for multiple data in a single notification as been recently introduced
  (See [PR 191](https://github.com/smartsdk/ngsi-timeseries-api/pull/191)),
  The following limitations still apply: a error in a single data entity will invalidate
  the all set. There is not optimisation for large message size.

- Data are assumed to be consistent. I.e., if the first data notification for
  an entity type use a given set of data types for the attributes, the following
  data notifications must be consistent, or they will be rejected. E.g. if
  the data type of attribute `speed` of entity type `car` is set initially
  to `Number`, later on it cannot be set to `Text`.
  
### Inserting data into QuantumLeap directly

To insert the data directly into quantum leap, we can use http://localhost:8668/v2/notify API, i.e. To notify QuantumLeap about the arrival of a new NGSI notification.

Consider the below example:

```
curl http://localhost:8668/v2/notify -s -S -H 'Content-Type: application/json' -d @- <<EOF
{ 
    "subscriptionId": "5ce3dbb331dfg9h71aad5deeaa", 
    "data": [ 
        { 
            "id": "Room1", 
            "temperature": 
               { 
                 "value": "10", 
                 "type": "Number" 
               }, 
             "pressure": 
               { 
                 "value": "12", 
                 "type": "Number" 
               }, 
            "type": "Room" 
        } 
    ] 
}
```

The data will be inserted into QuantumLeap successfully.

## Data Retrieval

To retrieve historical data from QuantumLeap, you can use the API endpoints
documented [here](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb).
Note there are a lot of possibilities, but not all of them are fully
implemented yet.

If you want to, you can interact directly with the database. For more details
refer to the [CrateDB](../admin/crate.md) section of the docs. What you need to
know in this case is that QuantumLeap will create one table per each entity
type. Table names are formed with a prefix (et) plus the lowercase version of
the entity type. I.e, if your entity type is *AirQualityObserved*, the
corresponding table name will be *etairqualityobserved*. Table names should be
prefixed also with the schema where they are defined. See the
[Multi-tenancy](#multi-tenancy) section below.

Finally, you can interact with your data visually using [Grafana](https://grafana.com/).
See the [Grafana](../admin/grafana.md) section of the docs to see how.

## Data Removal

You can remove historical data from QuantumLeap in two different ways.

- To remove all records of a given entity, use [this /entities delete API endpoint](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb).

- To remove all records of all entities of a given type, use [this /types delete API endpoint](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb).

Use the filters to delete only records in certain intervals of time.

## Multi-tenancy

QuantumLeap supports the use of different tenants, just like Orion does with
the usage FIWARE headers documented
[here](https://fiware-orion.readthedocs.io/en/master/user/multitenancy/index.html).

Recall the use of tenancy headers (`Fiware-Service` and `Fiware-ServicePath`) is
optional. Data insertion and retrieval will work by default without those.
However, if you use headers for the insertion, you need to specify the same ones
when querying data.

Note in the case of QuantumLeap, the headers at the time of insertion should
actually be used by the client at the time of creating the
[Subscription to Orion](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#subscriptions)
and also by the device when pushing data to Orion. As mentioned, the same
headers will have to be used in order to retrieve such data.

In case you are interacting directly with the database, you need to know that
QuantumLeap will use the `FIWARE-Service` as the
[database schema](https://crate.io/docs/crate/reference/en/latest/general/ddl/create-table.html?highlight=scheme#schemas)
for crate, with a specific prefix. This way, if you insert an entity of type
`Room` using the `Fiware-Service: magic` header, you should expect to find your
table as `mtmagic.etroom`. This information is also useful for example if you
are configuring the Grafana datasource, as explained in the
[Grafana section](../admin/grafana.md) of the docs.

## GeoCoding

This is an optional and experimental feature of QuantumLeap, which helps
harmonising the way location information is stored in the historical records.

The idea is that if entities arrive in QuantumLeap with an attribute of type
`StructuredValue` and named `address`, QuantumLeap interprets this as an address
field typically found in the [FIWARE Data Models](https://github.com/fiware/dataModels).
It then adds to the entity an attribute called `location` of the corresponding
geo-type. This means, if the address is a complete address with city,
street name and postal number, it maps that to a point and hence the generated
attribute will be of type `geo:point`. Without a postal number, the address
will represent the street (if any) or the city boundaries (if any) or even the
country boundaries. In these cases the generated location will be of the
`geo:json` form and will contain the values of such shapes.

**WARNING:** This feature uses [OpenStreetMap](https://www.openstreetmap.org)
and its Nominatim service. As such, you need to be aware of its
[copyright notes](https://www.openstreetmap.org/copyright) and most importantly
of their Usage Policies ([API Usage Policy](https://operations.osmfoundation.org/policies/api/)
and [Nominatim Usage Policy](https://operations.osmfoundation.org/policies/nominatim/)).
You should not abuse of this free service and you should cache your requests.
This is why you need to specify a cache in order to enable the geocoding.
QuantumLeap uses [Redis](https://redis.io/) for that.

So, to enable this feature, you need to pass (at initialisation time) to the
QuantumLeap container the environment variable `USE_GEOCODING` set to `True`
and the environment variables `REDIS_HOST` and `REDIS_PORT` respectively set to
the location of your REDIS instance and its access port. See the
[docker-compose-dev.yml](https://raw.githubusercontent.com/smartsdk/ngsi-timeseries-api/master/docker/docker-compose-dev.yml)
for example.
