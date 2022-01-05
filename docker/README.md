# QuantumLeap

[![FIWARE Core Context Management](https://nexus.lab.fiware.org/static/badges/chapters/core.svg)](https://www.fiware.org/developers/catalogue/)
[![Support](https://img.shields.io/badge/support-ask-yellowgreen.svg)](https://ask.fiware.org/questions/)

QuantumLeap is the first implementation of
[an API](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb) that supports the
storage of
[FIWARE NGSIv2](https://fiware.github.io/specifications/ngsiv2/stable/) data
into a
[time series database](https://en.wikipedia.org/wiki/Time_series_database). It
currently also experimentally supports the injection of
[NGSI-LD](https://www.etsi.org/deliver/etsi_gs/CIM/001_099/009/01.01.01_60/gs_CIM009v010101p.pdf)
in a backward compatible way with NGSI-v2 API. I.e. you can retrieve NGSI-LD
stored data via NGSI v2 API and retrieve data will be describe following NGSI v2
format.

QuantumLeap is not a
[real time](https://en.wikipedia.org/wiki/Real-time_computing) API, its purpose
is to process notifications received from the Context Broker and to create
temporal records for them. In general, the whole FIWARE stack, being based on a
micro-service architecture, cannot be regarded as real time in case you have
requirements on guaranteed delivery in a given amount of time.

## How to use this image

QuantumLeap must be instantiated and connected to an instance of the
[Orion Context Broker](https://fiware-orion.readthedocs.io/en/latest/), a sample
`docker-compose` file can be found below.

```yaml
version: "3"

services:
    orion:
        image: fiware/orion
        ports:
            - "1026:1026"
        command: -logLevel DEBUG -noCache -dbhost mongo
        depends_on:
            - mongo
        healthcheck:
            test: ["CMD", "curl", "-f", "http://0.0.0.0:1026/version"]
            interval: 1m
            timeout: 10s
            retries: 3

    quantumleap:
        image: orchestracities/quantumleap
        ports:
            - "8668:8668"
        depends_on:
            - mongo
            - orion
            - crate
        environment:
            - CRATE_HOST=${CRATE_HOST:-crate}
            - USE_GEOCODING=True
            - REDIS_HOST=redis
            - REDIS_PORT=6379
            - LOGLEVEL=DEBUG

    mongo:
        image: mongo:${MONGO_VERSION:4.4}
        ports:
            - "27017:27017"
        volumes:
            - mongodata:/data/db

    crate:
        image: crate:${CRATE_VERSION:-4.6.5}
        command:
            crate -Cauth.host_based.enabled=false -Ccluster.name=democluster
            -Chttp.cors.enabled=true -Chttp.cors.allow-origin="*"
        environment: LOG4J_FORMAT_MSG_NO_LOOKUPS=true
        ports:
            # Admin UI
            - "4200:4200"
            # Transport protocol
            - "4300:4300"
        volumes:
            - cratedata:/data

    grafana:
        image: grafana/grafana
        ports:
            - "3000:3000"
        depends_on:
            - crate

    redis:
        image: redis:${REDIS_VERSION:-4}
        ports:
            - "6379:6379"
        volumes:
            - redisdata:/data

volumes:
    mongodata:
    cratedata:
    redisdata:

networks:
    default:
```

## Configuration with environment variables

Many settings can be configured using Docker environment variables. A typical
QuantumLeap Docker container is driven by environment variables such as those
shown below:

- `CRATE_HOST` - CrateDB Host
- `CRATE_PORT` - CrateDB Port
- `CRATE_DB_USERNAME` - CrateDB Username
- `CRATE_DB_PASSWORD` - CrateDB Password
- `POSTGRES_HOST` - PostgreSQL Host
- `POSTGRES_PORT` - PostgreSQL Port
- `POSTGRES_DB_NAME` - PostgreSQL default db
- `POSTGRES_DB_USER` - PostgreSQL user
- `POSTGRES_DB_PASS` - PostgreSQL password
- `POSTGRES_USE_SSL` - t or f enable SSL
- `REDIS_HOST` - Redis Host
- `REDIS_PORT` - Redis Port

A full list can be found in the
[Quantum Leap Documentation](https://quantumleap.readthedocs.io/en/latest/admin/configuration/#environment-variables)

## How to build an image

The
[Dockerfile](https://github.com/orchestracities/ngsi-timeseries-api/blob/master/docker/Dockerfile)
associated with this image can be used to build an image in several ways:

- By default, the `Dockerfile` retrieves the **latest** version of the
    codebase direct from GitHub (the `build-arg` is optional):

```console
docker build -t quantumleap . --build-arg DOWNLOAD=latest
```

- You can alter this to obtain the last **stable** release run this
    `Dockerfile` with the build argument `DOWNLOAD=stable`

```console
docker build -t quantumleap . --build-arg DOWNLOAD=stable
```

- You can also download a specific release by running this `Dockerfile` with
    the build argument `DOWNLOAD=<version>`

```console
docker build -t quantumleap . --build-arg DOWNLOAD=1.7.0
```

## Building from your own fork

To download code from your own fork of the GitHub repository add the
`GITHUB_ACCOUNT`, `GITHUB_REPOSITORY` and `SOURCE_BRANCH` arguments (default
`master`) to the `docker build` command.

```console
docker build -t quantumleap . \
    --build-arg GITHUB_ACCOUNT=<your account> \
    --build-arg GITHUB_REPOSITORY=<your repo> \
    --build-arg SOURCE_BRANCH=<your branch>
```

## Building from your own source files

Alternatively, if you want to build directly from your own sources, please copy
the existing `Dockerfile` into file the root of the repository and amend it to
copy over your local source using :

```Dockerfile
COPY . /opt/quantumleap/
```

Full instructions can be found within the `Dockerfile` itself.

## Building using an alternative sources and Linux Distros

The `Dockerfile` is flexible enough to be able to use
[alternative base images](https://kuberty.io/blog/best-os-for-docker/) should
you wish. The base image defaults to using the `alpine` distro, but other base
images can be injected using `--build-arg` parameters on the commmand line. For
example, to create a container based on
[Red Hat UBI (Universal Base Image) 8](https://developers.redhat.com/articles/2021/11/08/optimize-nodejs-images-ubi-8-nodejs-minimal-image)
add `BUILDER`, `DISTRO`, `PACKAGE_MANAGER` and `USER` parameters as shown:

```console
docker build -t quantumleap \
  --build-arg BUILDER=registry.access.redhat.com/ubi8/nodejs-14 \
  --build-arg DISTRO=registry.access.redhat.com/ubi8/nodejs-14-minimal \
  --build-arg PACKAGE_MANAGER=yum \
  --build-arg USER=1001 . --no-cache
```

To create a container based on [Debian Linux](https://alpinelinux.org/about/)
add `BUILDER`, `DISTRO`, `PACKAGE_MANAGER` parameters as shown:

```console
docker build -t quantumleap \
  --build-arg BUILDER=python:3.8 \
  --build-arg DISTRO=python:3.8-slim \
  --build-arg PACKAGE_MANAGER=apt . --no-cache
```

Currently, the following `--build-arg` parameters are supported:

| Parameter           | Description                                                                                                                                 |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `BUILDER`           | Preferred [linux distro](https://kuberty.io/blog/best-os-for-docker/) to use whilst building the image, defaults to `python:3.8-alpine`     |
| `DISTRO`            | Preferred [linux distro](https://kuberty.io/blog/best-os-for-docker/) to use for the final container image, defaults to `python:3.8-alpine` |
| `DOWNLOAD`          | The GitHub SHA or tag to download - defaults to `latest`                                                                                    |
| `GITHUB_ACCOUNT`    | The GitHub Action to download the source files from, defaults to `orchestracities`                                                          |
| `GITHUB_REPOSITORY` | The name of the GitHub repository to download the source files from, defaults to `ngsi-timeseries-api`                                      |
| `PACKAGE_MANAGER`   | Package manager to use whilst creating the build, defaults to `apt`                                                                         |
| `SOURCE_BRANCH`     | The GitHub repository branch to download the source files from, defaults to `master`                                                        |

## Container Command Arguments

You can also pass any valid Gunicorn option as container command arguments to
add or override options in `server/gconfig.py` ---see `server.grunner` for the
details. In particular, a convenient way to reconfigure Gunicorn is to mount a
config file on the container and then run the container with the following
option

```console
    --config /path/to/where/you/mounted/your/gunicorn.conf.py
```

as in the below example

```console
echo 'workers = 2' > gunicorn.conf.py
docker run -it --rm \
     -p 8668:8668 \
     -v $(pwd)/gunicorn.conf.py:/gunicorn.conf.py
     quantumleap --config /gunicorn.conf.py
```
