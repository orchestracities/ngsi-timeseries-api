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
from the sections below which fits yours.

## Deploy QuantumLeap on a single-host for local testing

Follow these steps if you want to quickly deploy all the components of the
[typical scenario](../index.md) at once, to start experimenting with
QuantumLeap ASAP.

**Important:** Do not use this approach for production environments.

Download (or create locally) a copy of [this docker-compose.yml](https://raw.githubusercontent.com/smartsdk/ngsi-timeseries-api/master/docker/docker-compose-dev.yml)
file. Then start it up:

```
# same path were you have placed the docker-compose-dev.yml
$ docker stack deploy -c docker-compose-dev.yml ql
```

**NOTE:** If you are using an old docker version, it might be the case that your
local docker daemon is not running in the **swarm mode** and the above command
fails. You can either update your docker installation (suggested), enable the
**swarm mode** executing `docker swarm init` or ultimately fall back to
deploying using **docker-compose**
(`docker-compose -f docker-compose-dev.yml up -d`).

After a while, check that all containers are running (up):

```
$ docker service ls
ID                  NAME                MODE                REPLICAS            IMAGE                         PORTS
zpkl93c67ix1        ql_crate            replicated          1/1                 crate:1.0.5                   *:4200->4200/tcp, *:4300->4300/tcp
s3dkplowfvhy        ql_grafana          replicated          1/1                 grafana/grafana:latest        *:3000->3000/tcp
afdrgwc4eo1r        ql_mongo            replicated          1/1                 mongo:3.2                     *:27017->27017/tcp
l32fn6yft42q        ql_orion            replicated          1/1                 fiware/orion:1.13.0           *:1026->1026/tcp
gcm1lszuj2k8        ql_quantumleap      replicated          1/1                 smartsdk/quantumleap:latest   *:8668->8668/tcp
rrnd03qqb2il        ql_redis            replicated          1/1                 redis:latest                  *:6379->6379/tcp
```

Now you're ready to use QuantumLeap as instructed in the [User Manual](../user/index.md).

When you are done experimenting, remember to teardown the stack.

```
$ docker stack rm ql
```

## Deploy QuantumLeap in HA on a Docker Swarm cluster

To deploy QuantumLeap services in HA as a service on a Docker Swarm Cluster,
you can follow the instructions in [this repository](https://smartsdk.github.io/smartsdk-recipes/data-management/quantumleap/readme/).

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
*Crate*, so you need to provide a reachable hostname where Crate is running.
By default QL will append the port `4200` to the hostname. You can of course
add your required environment variables with `-e`. For more options see [docker run reference](https://docs.docker.com/engine/reference/run/).
