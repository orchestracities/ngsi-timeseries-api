# Used Ports

The table below summarises the default ports for each of the services typically
used with QuantumLeap. So, if you run them behind firewalls, remember to
include the corresponding rules.

| Protocol          | Port          | Description|
| -------------     |:-------------:| :-----|
|TCP| 1026|  Orion CB |
|TCP| 8668|  QuantumLeap's API |
|TCP| 3000|  Grafana |

Just FYI, the following ones should not be typically exposed to the outside but
are used within the cluster.

| Protocol          | Port          | Description|
| -------------     |:-------------:| :-----|
|TCP                | 27017         |  Mongo database |
|TCP                | 4200          |  CrateDB Admin UI |
|TCP                | 4300          |  CrateDB Transport Protocol |
|TCP                | 5432          |  PostgreSQL Protocol |
|TCP                | 6379          |  Redis cache (used by geocoding) |

For more info on ports numbers, you can always inspect the ports being exposed
in the [docker-compose-dev.yml](https://raw.githubusercontent.com/orchestracities/ngsi-timeseries-api/master/docker/docker-compose-dev.yml)
file of this repo (actually the one you used to deploy, of course).
