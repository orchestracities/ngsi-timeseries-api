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

        curl -X GET http://0.0.0.0:1026/version -H 'Accept: application/json'

    You should get a return status `200 OK`.

1. Check you can get *QuantumLeap version*

        curl -X GET http://0.0.0.0:8668/v2/version -H 'Accept: application/json'

    You should get a return status `200 OK`.

1. Create an Orion Subscription via "QuantumLeap Subscribe"
        curl -X POST \
        'http://0.0.0.0:8668/v2/subscribe?orionUrl=http://orion:1026/v2&quantumleapUrl=http://quantumleap:8668/v2&entityType=AirQualityObserved' \
        -H 'Accept: application/json'

    Note we've just created a subscription for any change in any attribute of
    entities of type [AirQualityObserved](https://github.com/Fiware/dataModels/tree/master/Environment/AirQualityObserved)

    You should get a return status `201 Created`.

1. Check you cat get such subscription from Orion

        curl -X GET http://0.0.0.0:1026/v2/subscriptions \
        -H 'Accept: application/json'

    You should get a return status `200 OK`.

1. Insert an entity of AirQualityObserved into Orion

        curl -X POST \
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

    You should get a return status `201 Created`.

    Note we used `options=keyValues` for simplification just because this is a
    sanity check. If you use such option in practice, you may loose translation capabilities as explained in the [user guide](../user/index.md#orion-subscription).

1. Update the precipitation value of the same entity in Orion.

        curl -X PATCH \
        http://0.0.0.0:1026/v2/entities/air_quality_observer_be_001/attrs \
        -H 'Accept: application/json' \
        -H 'Content-Type: application/json' \
        -d '{
        "precipitation": {
        "value": 100,
        "type": "Number"
        }
        }'

    You should get a return status `204 No Content`.

1. Query again historical records of precipitation for the same entity (1T1E1A).

        curl -X GET \
        'http://0.0.0.0:8668/v2/entities/air_quality_observer_be_001/attrs/precipitation?type=AirQualityObserved' \
        -H 'Accept: application/json'

    You should get a return status `200 OK`, plus the historical records in the
    response body.

1. Finally, to tidy things up, you can delete all created records.

    Delete records from QL

        curl -X DELETE http://0.0.0.0:8668/v2/types/AirQualityObserved

    Delete entity from Orion

        curl -X DELETE \
        http://0.0.0.0:1026/v2/entities/air_quality_observer_be_001 \
        -H 'Accept: application/json'

    Delete subscription from Orion (replace the `id` with yours)

        curl -X DELETE \
        http://0.0.0.0:1026/v2/subscriptions/5b3df2ae940fcc446763ef90 \
        -H 'Accept: application/json'

## Automated Sanity Check

If you are already familiar with the flow and just want a quick way to check
the essential services are correctly deployed, you can make use of one of the
integration tests that checks exactly this connection among core components.

*IMPORTANT:* It is not suggested to run this script in production deployments
with valuable data. If things go wrong in the test, it may leave garbage data
or can lead to data loses. As always, use automation with caution.

You can see the test script [here](https://github.com/smartsdk/ngsi-timeseries-api/blob/master/tests/test_integration.py).
Pay attention to the input variables that, depending on your deployment, you
may need to configure. These indicate the URLs where to find the core services.
By default, it assumes all services run in a local docker-based deployment.

You can quickly execute the test in a container as shown below. You will have to
adjust, of course, the urls so that they point to your deployed services. In
the following example, ORION and QL are reachable by the test container at
`192.0.0.1` and then, by default, ORION and QL find each other at `orion` and
`quantumleap` endpoints because both were deployed in the same docker network.

```
docker run -ti --rm -e ORION_URL="http://192.0.0.1:1026" -e QL_URL="http://192.0.0.1:8668" quantumleap pytest tests/test_integration.py
```

Or, assuming all services are in the same docker deployment and you have access
to it, you can run the test container in the same network so as to use the
service names in the urls.

```
docker run -ti --rm --network docker_default -e ORION_URL="http://orion:1026" -e QL_URL="http://quantumleap:8668" quantumleap pytest tests/test_integration.py
```
