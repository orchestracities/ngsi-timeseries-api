# Sanity Check

To make sure your deployment of QuantumLeap is complete and well functioning,
you can follow any of these sanity checks.

The instructions assume a local docker-based deployment with the ports mapped to
localhost. But of course, you will need to update the IP addresses of the
services accordingly to suit your deployment.

## Manual Sanity Check

Following the process manually can help you get acquainted with the flow. To
assist you, you can use the *Orion* and *QuantumLeap* requests in [this postman collection](https://raw.githubusercontent.com/smartsdk/smartsdk-recipes/master/recipes/tools/postman_collection.json).
If you don't use Postman, you can use the equivalent curl commands bellow.

1. Check you can get *Orion version*

    ```bash
    curl -X GET http://0.0.0.0:1026/version -H 'Accept: application/json'
    ```

    You should get a return status `200 OK`.

1. Check you can get *QuantumLeap version*

    ```bash
    $ curl -X GET http://0.0.0.0:8668/version -H 'Accept: application/json'
    ```

    You should get a return status `200 OK`.

1. Create an Orion Subscription via "Orion Subscriptions" as described
    in [Orion docs](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#subscriptions)

    ```bash
    $ curl -X POST \
    'http://0.0.0.0:1026/v2/subscriptions \
    -H 'Accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "description": "A subscription to get info about Room1",
    "subject": {
      "entities": [
        {
          "id": ".*",
          "type": "AirQualityObserved"
        }
      ],
      "condition": {
        "attrs": [
        ]
      }
    },
    "notification": {
      "http": {
        "url": "http://quantumleap:8668/v2/notify"
      },
      "attrs": [
      ]
    },
    "expires": "2040-01-01T14:00:00.00Z"
    ```

    Note we've just created a subscription for any change in any attribute of
    entities of type [AirQualityObserved](https://github.com/FIWARE/data-models/tree/master/specs/Environment/AirQualityObserved).
    You should get a return status `201 Created`.

1. Check you cat get such subscription from Orion

    ```bash
    $ curl -X GET http://0.0.0.0:1026/v2/subscriptions \
    -H 'Accept: application/json'
    ```

    You should get a return status `200 OK`.

1. Insert an entity of AirQualityObserved into Orion

    ```bash
    $ curl -X POST \
    'http://0.0.0.0:1026/v2/entities?options=keyValues' \
    -H 'Accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "id": "air_quality_observer_be_001",
    "type": "AirQualityObserved",
    "address": {
    "streetAddress": "IJzerlaan",
    "postOfficeBoxNumber": "18",
    "addressLocality": "Antwerpen",
    "addressCountry": "BE"
    },
    "dateObserved": "2017-11-03T12:37:23.734827",
    "source": "http://testing.data.from.smartsdk",
    "precipitation": 0,
    "relativeHumidity": 0.54,
    "temperature": 12.2,
    "windDirection": 186,
    "windSpeed": 0.64,
    "airQualityLevel": "moderate",
    "airQualityIndex": 65,
    "reliability": 0.7,
    "CO": 500,
    "NO": 45,
    "NO2": 69,
    "NOx": 139,
    "SO2": 11,
    "CO_Level": "moderate",
    "refPointOfInterest": "null"
    }'
    ```

    You should get a return status `201 Created`.

    Note we used `options=keyValues` for simplification just because this is a
    sanity check. If you use such option in practice, you may loose translation
    capabilities as explained in the [user guide](../user/using.md#orion-subscription).

1. Update the precipitation value of the same entity in Orion.

    ```bash
    $ curl -X PATCH \
    http://0.0.0.0:1026/v2/entities/air_quality_observer_be_001/attrs \
    -H 'Accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "precipitation": {
    "value": 100,
    "type": "Number"
    }
    }'
    ```

    You should get a return status `204 No Content`.

1. Query again historical records of precipitation for the same entity (1T1E1A).

    ```bash
    $ curl -X GET \
    'http://0.0.0.0:8668/v2/entities/air_quality_observer_be_001/attrs/precipitation?type=AirQualityObserved' \
    -H 'Accept: application/json'
    ```

    You should get a return status `200 OK`, plus the historical records in the
    response body.

1. Finally, to tidy things up, you can delete all created records.

    Delete records from QuantumLeap

    ```bash
    $ curl -X DELETE http://0.0.0.0:8668/v2/types/AirQualityObserved
    ```

    Delete entity from Orion

    ```bash
    $ curl -X DELETE \
    http://0.0.0.0:1026/v2/entities/air_quality_observer_be_001 \
    -H 'Accept: application/json'
    ```

    Delete subscription from Orion (replace the `id` with yours)

    ```bash
    $ curl -X DELETE \
    http://0.0.0.0:1026/v2/subscriptions/5b3df2ae940fcc446763ef90 \
    -H 'Accept: application/json'
    ```

## Automated Sanity Check

If you are already familiar with the flow and just want a quick way to check
the essential services are correctly deployed, you can make use of one of the
integration tests that checks exactly this connection among core components.

**IMPORTANT:** It is not suggested to run this script in production deployments
with valuable data. If things go wrong in the test, it may leave garbage data
or can lead to data loses. As always, use automation with caution.

You can see the test script [here](https://github.com/orchestracities/ngsi-timeseries-api/blob/master/src/tests/test_integration.py).
Pay attention to the input variables that, depending on your deployment, you
may need to configure. These indicate the URLs where to find the core services.
By default, it assumes all services run in a local docker-based deployment.

You can quickly execute the test in a container as shown below. You will have to
adjust, of course, the urls so that they point to your deployed services. In
the following example, Orion and QuantumLeap are reachable by the test container
at `192.0.0.1` and then, by default, Orion and QuantumLeap find each other at
`orion` and `quantumleap` endpoints because both were deployed in the same
docker network.

```bash
$ docker run -ti --rm -e ORION_URL="http://192.0.0.1:1026" -e QL_URL="http://192.0.0.1:8668" quantumleap pytest tests/test_integration.py
```

Or, assuming all services are in the same docker deployment and you have access
to it, you can run the test container in the same network so as to use the
service names in the urls.

```bash
$ docker run -ti --rm --network docker_default -e ORION_URL="http://orion:1026" -e QL_URL="http://quantumleap:8668" quantumleap pytest tests/test_integration.py
```
