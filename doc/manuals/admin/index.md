# Installing

At the moment, the only actively supported distribution of QuantumLeap is Docker. Though, you can build and install it from sources, but no guidance is provided for such installation at the moment.

If you need to install Docker, refer to [Docker Installation](https://docs.docker.com/engine/installation/).

You might also need docker-compose for some cases, which can be installed by running:

    # Replace 1.16.0 with the version you want. We suggest the latest from https://github.com/docker/compose/releases
    curl -L https://github.com/docker/compose/releases/download/1.16.0/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

Alternatively, see the docker-compose [install docs](https://docs.docker.com/compose/install/) for more install options and instructions.

The QuantumLeap Docker Image is hosted at [https://hub.docker.com/r/smartsdk/quantumleap/](https://hub.docker.com/r/smartsdk/quantumleap/).

Now, depending on your scenario, you might have different needs. See from the sections below which fits yours.

## Deploy QuantumLeap in HA on a Docker Swarm cluster

To deploy QuantumLeap services in HA as a service on a Docker Swarm Cluster, you can follow the instructions in [this repository](https://smartsdk.github.io/smartsdk-recipes/data-management/quantumleap/readme/).

There you will find instructions on how to deploy not only QuantumLeap but also all the complementary services that typically form part of the deployment scenario.

## Deploy QuantumLeap using docker-compose (for testing)

If you want to quickly deploy all the components of the [typical scenario](../index.md) at once to start experimenting with QuantumLeap ASAP, do the following. __Important__: Do not follow this approach for production environments.

Download (or create locally) a copy of [this docker-compose.yml](https://raw.githubusercontent.com/smartsdk/ngsi-timeseries-api/master/experiments/grafana/docker-compose.yml) file.

Then start it up:

    # same path were you have placed the docker-compose.yml
    $ docker-compose up -d

After a while, check that all containers are running (up):

    $ docker ps
    CONTAINER ID        IMAGE                  COMMAND                  CREATED              STATUS                        PORTS                                                           NAMES
    2ef89b11dd7f        smartsdk/quantumleap   "/bin/sh -c 'pytho..."   About a minute ago   Up About a minute             0.0.0.0:8668->8668/tcp                                          grafana_quantumleap_1
    f435868ea042        grafana/grafana        "/run.sh"                About a minute ago   Up About a minute             0.0.0.0:3000->3000/tcp                                          grafana_grafana_1
    7bea4ea0b8b4        fiware/orion:1.7.0     "/usr/bin/contextB..."   About a minute ago   Up About a minute (healthy)   0.0.0.0:1026->1026/tcp                                          grafana_orion_1
    337cd5b38b82        crate:1.0.5            "/docker-entrypoin..."   About a minute ago   Up About a minute             0.0.0.0:4200->4200/tcp, 0.0.0.0:4300->4300/tcp, 5432-5532/tcp   grafana_crate_1
    be4a72523e69        mongo:3.2              "docker-entrypoint..."   About a minute ago   Up About a minute             0.0.0.0:27017->27017/tcp                                        grafana_mongo_1

Now you're ready to use QuantumLeap as instructed in the [User Manual](../user/index.md).

When you are done experimenting, remember to teardown the compose.

    $ docker-compose down -v


### Reuse External Orion Instance

If you have already Orion running somewhere else and you just want to deploy QuantumLeap, you can proceed as explained in the previous sections, but before running ```docker-compose up``` remove from the `docker-compose.yml` file the complete definition of the ```orion:``` and ```mongo:``` services. You will also need to remove the references to them in the ```depends_on:``` section of the other services.

Similarly, if you don't want to use *grafana*, you can remove that service definition as well.

This way, your `docker-compose.yml` file ends up more or less with the following sections only

    version: '3'

    services:
        quantumleap:
            ...
        crate:
            ...

    networks:
        ...

### Reuse External Orion and CrateDB

If you only need to run QuantumLeap to complete your setup, you can simply run

    docker run -d -p 8668:8668 -e "CRATE_HOST=http://your_crate_location" smartsdk/quantumleap

The environment variable `CRATE_HOST` will tell QuantumLeap where to reach *Crate*, so you need to provide a reachable hostname where Crate is running. By default QL will append the port `4200` to the hostname.

For more options see [docker run reference](https://docs.docker.com/engine/reference/run/).
