# Usage Overview

First you need to have QuantumLeap runnning (of course). Refer to the [Installation Manual](../admin/index.md) for instructions.

Then, you need to connect Orion Context Broker to QuantumLeap through a subscription for each Entity Type whose historical data you are interested in. Historical data for each entity type will be persisted as long as the subscription is active.

The flow is therefore the following

- Create an Orion subscription for each entity type of your interest once
- Insert and update your data to Orion as usual
- Done, your historical data will be persisted in QuantumLeap's database.

Let's have a look in more detail of each step.


# Orion Subscription

As stated before, the link between Orion and QuantumLeap is established through a subscription you need to create. It is therefore important that you understand well how the NGSIv2 Subscription mechanism works. This is carefully explained in the corresponding section of [Orion docs](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#subscriptions).

Here's an example of the payload of the subscription you need to create in Orion to establish the link Orion-QuantumLeap.

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
                "url": "http://quantumleap:8668/notify"
            },
            "attrs": [
            "temperature"
            ],
            "metadata": ["dateCreated", "dateModified"]
        },
        "throttling": 5
    }

Important things to notice from the example.

- You can create any valid NGSI subscription for your entities.

- Though not compulsory, it is highly recommended to include the ```"metadata": ["dateCreated", "dateModified"]``` part in the *"notification"* part of the subscription. This instructs Orion to include the modification time of the attributes in the notification. This timestamp will be used as the time index in the database. If this is somehow missing, QuantumLeap will use its current system time at which the notification arrived, which might not be exactly what you want.

- Notifications must come in complete [NGSI JSON Entity Representation](http://docs.orioncontextbroker.apiary.io/#introduction/specification/json-attribute-representation) form. Other forms, such as the [simplified entity representation](http://docs.orioncontextbroker.apiary.io/#introduction/specification/simplified-entity-representation) are not supported by QL because they lack information on attribute types, required by QL to make proper translations. This means, don't use options like ```"attrsFormat": "keyValues"```

- The ```"url"``` field of the subscription specifies where Orion will send the notifications. I.e, this must be QuantumLeap's */notify* endpoint. By default, QuantumLeap listens at port 8668.


# Data Insertion

Now you are ready to insert (or keep updating) your entities as you've always done in Orion Context Broker. Refer to the [docs](http://fiware-orion.readthedocs.io/en/latest/user/walkthrough_apiv2/index.html#issuing-commands-to-the-broker) for more instructions.

It's not a problem if the first insert was done before you created the subscription. Of course, you will get historical records of the updates happening after the subscription was created.

Here's an example of an insert payload that will generate a notification based on the subscription example shown before.

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
    }


### Attributes DataType Translation

NGSI Attribute types typically used can be seen in the *Specification* section of the [NGSI API](http://telefonicaid.github.io/fiware-orion/api/v2/latest/). The table below shows which attribute types will be translated to which [Crate Data Types](https://crate.io/docs/crate/reference/sql/data_types.html).

| NGSI Type          | Crate Datatype          | Observation |
| ------------- |:-------------:| :-----|
|Array               | [array(string)](https://crate.io/docs/crate/reference/sql/data_types.html#array)           | TODO: Support arrays of other types. |
|Boolean             | [boolean](https://crate.io/docs/crate/reference/sql/data_types.html#boolean)                 | - |
|DateTime             | [timestamp](https://crate.io/docs/crate/reference/sql/data_types.html#timestamp)                 | - |
|Integer             | [long](https://crate.io/docs/crate/reference/sql/data_types.html#numeric-types)                    | TODO: Fix this inconsistency ASAP! |
|geo:json            | [geo_shape](https://crate.io/docs/crate/reference/sql/data_types.html#geo-shape)               | NGSI Simple Location Format is not yet supported. Use GeoJSON instead. Read more [here](http://docs.orioncontextbroker.apiary.io/#introduction/specification/geospatial-properties-of-entities).|
|Number              | [float](https://crate.io/docs/crate/reference/sql/data_types.html#numeric-types)                   |-|
|Text                | [string](https://crate.io/docs/crate/reference/sql/data_types.html#string)                  | This is the default type if the provided type is unknown. |
|StructuredValue     | [object](https://crate.io/docs/crate/reference/sql/data_types.html#object)                  |-|

If the type of any of the received attributes is not present in the column *NGSI Type* of the previous table, the value of such attribute will be treated internally as a string.

NOTE: Attributes metadata are still not being persisted.


# Data Retrieval

The QuantumLeap endpoints to retrieve data are still to be developed.

However, you can already query the persisted data either directly interacting with the Crate database, or through the use of Grafana. Further details are explained in the [Crate](../admin/crate.md) and [Grafana](../admin/grafana.md) sections, respectively.

What you need to know in the mean time is that QuantumLeap will create one table per each entity type. Table names are formed with the "et" prefix plus the lowercase version of the entity type. I.e, if your entity type is *AirQualityObserved*, the corresponding table name will be *etairqualityobserved*. All created tables for now belong to the default "doc" schema.

### Restrictions

- You cannot have two entity types with the same name but different capitalization. E.g: `Preprocessor` and `Processor`. The same applies for attribute names of a given entity. I.e, attributes `hotSpot` and `hotspot` will be treated as the same. These are rare corner-cases, but it is worth keeping in mind this. Ultimately, the correct naming of types and attributes should respect the naming guidelines explained [here](http://fiware-datamodels.readthedocs.io/en/latest/guidelines/index.html).

### The Time Index

A fundamental index in the timeseries database is the time index. You may be wondering... where is it stored?

QuantumLeap will persist the time index for each notification in a special column called ```time_index```.  If you payed attention in the *Orion Subscription* section, you know at least which value is used as the time index. This is, the ```"dateModified"``` value notified by Orion or, if you missed that option in the subscription, the notification arrival time.

In the future, this could be more flexible and allow users to define any Datetime attribute to be used as the time index.
