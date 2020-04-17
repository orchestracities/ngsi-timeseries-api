# Installing

At the moment, the only actively supported distribution of QuantumLeap is based
on Docker. You could build and install it from sources, but no guidance is
provided for such installation at the moment.

If you need to install Docker, refer to the [Docker Installation](https://docs.docker.com/engine/installation/).
To check it works, you should be able to successfully run...

```
docker --version
```

You might also need [docker-compose](https://docs.docker.com/compose/) for
some cases. Checkout the [install docs](https://docs.docker.com/compose/install/).
To check it works, you should be able to successfully run...

```
docker-compose --version
```

The QuantumLeap Docker Image is hosted at [https://hub.docker.com/r/smartsdk/quantumleap/](https://hub.docker.com/r/smartsdk/quantumleap/).

Now, depending on your scenario, you have different deployment options. See
from the sections below which fits yours. After installation, you can check
everything is working as expected by following the [Sanity Check](check.md).

## Deploy QuantumLeap on a single-host for local testing

Follow these steps if you want to quickly deploy all the components of the
[typical scenario](../index.md) at once, to start experimenting with
QuantumLeap ASAP.

**Important:** Do not use this approach for production environments.

Download (or create locally) a copy of [this docker-compose.yml](https://raw.githubusercontent.com/smartsdk/ngsi-timeseries-api/master/docker/docker-compose-dev.yml)
file. Then start it up:

```
# same path were you have placed the docker-compose-dev.yml
$ docker-compose -f docker-compose-dev.yml up -d
```

After a while, check that all containers are up and running:

```
$ docker ps
CONTAINER ID        IMAGE                  COMMAND                  CREATED             STATUS                   PORTS                                                           NAMES
8cf0b544868d        smartsdk/quantumleap   "/bin/sh -c 'python …"   2 minutes ago       Up 2 minutes             0.0.0.0:8668->8668/tcp                                          docker_quantumleap_1
aa09dbcb8500        fiware/orion:1.13.0    "/usr/bin/contextBro…"   2 minutes ago       Up 2 minutes (healthy)   0.0.0.0:1026->1026/tcp                                          docker_orion_1
32709dbc5701        grafana/grafana        "/run.sh"                2 minutes ago       Up 2 minutes             0.0.0.0:3000->3000/tcp                                          docker_grafana_1
ed9f8a60b6e8        crate:1.0.5            "/docker-entrypoint.…"   2 minutes ago       Up 2 minutes             0.0.0.0:4200->4200/tcp, 0.0.0.0:4300->4300/tcp, 5432-5532/tcp   docker_crate_1
76de9d756b7d        mongo:3.2              "docker-entrypoint.s…"   2 minutes ago       Up 2 minutes             0.0.0.0:27017->27017/tcp                                        docker_mongo_1
92e2129fec9b        redis                  "docker-entrypoint.s…"   2 minutes ago       Up 2 minutes             0.0.0.0:6379->6379/tcp                                          docker_redis_1
```

Now you're ready to use QuantumLeap as instructed in the [User Manual](../user/index.md).

When you are done experimenting, remember to teardown things.

```
# same path were you have placed the docker-compose-dev.yml
$ docker-compose -f docker-compose-dev.yml down -v
```

## Deploy QuantumLeap in HA on a Docker Swarm cluster

To deploy QuantumLeap services in HA as a service on a Docker Swarm Cluster,
you can follow the instructions in [this repository](https://smartsdk-recipes.readthedocs.io/en/latest/data-management/quantumleap/readme/).

There, you will find instructions on how to deploy in HA not only
**QuantumLeap** but also all the complementary services that typically form
part of the deployment scenario.

## Deploy QuantumLeap reusing external services instances

If you have already Orion running somewhere else and you just want to deploy
QuantumLeap, you can proceed as explained in the previous sections, but before
deploying, remove from the docker-compose file the complete definition of
the `orion:` and `mongo:` services. You will also need to remove the
references to them in the `depends_on:` section of the other services.

Similarly, if you don't want to use some of the complementary services, like
**grafana**, you can remove such services definition as well. Ultimately, the
only required services for a minimal functioning QL are `quantumleap` and the
time-series database (`crate` in the common case).

Alternatively, if you only need to run QuantumLeap to complete your setup, you
can simply run

```
docker run -d -p 8668:8668 -e "CRATE_HOST=http://your_crate_location" smartsdk/quantumleap
```

The environment variable `CRATE_HOST` will tell QuantumLeap where to reach
*CrateDB*, so you need to provide a reachable hostname where CrateDB is running.
By default QL will append the port `4200` to the hostname. You can of course
add your required environment variables with `-e`. For more options see
[docker run reference](https://docs.docker.com/engine/reference/run/).

## Deploy QuantumLeap in Kubernetes

To deploy QuantumLeap services in Kubernetes,
you can leverage the Helm Charts in [this repository](https://smartsdk-recipes.readthedocs.io/en/latest/data-management/quantumleap/readme/).

In particular you will need to deploy:
* [CrateDB](https://github.com/orchestracities/charts/tree/master/charts/crate)
* [Optional] Timescale - for which you can refer to [Patroni Helm Chart](https://github.com/helm/charts/tree/master/incubator/patroni).
* [QuantumLeap](https://github.com/orchestracities/charts/tree/master/charts/quantumleap)

## FIWARE Releases Compatibility

The current version of QuantumLeap is compatible with any FIWARE release
greater than `6.3.1`. More info of FIWARE releases can be seen [here](https://forge.fiware.org/plugins/mediawiki/wiki/fiware/index.php/Releases_and_Sprints_numbering,_with_mapping_to_calendar_dates).

To check which versions of the Generic Enablers and external dependencies QL is
used and tested, checkout the
[docker-compose-dev.yml](https://raw.githubusercontent.com/smartsdk/ngsi-timeseries-api/master/docker/docker-compose-dev.yml)
file used for the deployment.
