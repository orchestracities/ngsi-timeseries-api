# Quantumleap

[![Build Status](https://travis-ci.org/smartsdk/ngsi-timeseries-api.svg?branch=master)](https://travis-ci.org/smartsdk/ngsi-timeseries-api)
[![Docker Status](https://img.shields.io/docker/pulls/smartsdk/quantumleap.svg)](https://hub.docker.com/r/smartsdk/quantumleap/)


## Introduction

Quantumleap is an adapter aimed to bring NGSIv2 Historical Data on top of TimeSeries Databases.

In the end, its goal is similar to those of [FIWARE's Comet STH](https://fiware-sth-comet.readthedocs.io/en/latest/
). However, Comet does not yet support NGSIv2, it's tied to MongoDB, and some of the conditions and constraints under which it was developed are no longer hold. There is nothing wrong with it, this is just an exploration on a new way to provide historical data for NGSI.

We have decided to focus on the NGSIv2-CrateDB translator for now because we find in [CrateDB](www.crate.io) the following advantages:
- Easy scalability with containerized database cluster out of the box
- Geo-queries support out of the box
- Nice SQL-like querying language to work with
- Supported integration with visualization tools like [Grafana](www.grafana.com)

## How it works

The idea of Quantumleap is pretty straigtforward. It consumes [Context Broker](https://fiware-orion.readthedocs.io
) notifications in NGSI JSON Entity Representation, and translates them to inserts executed on a times-series oriented database.

So, the first step is to create an Orion Subscription for the entities care about having historical data. This is explained in [the corresponding section of Orion docs](https://fiware-orion.readthedocs.io/en/master/user/walkthrough_apiv2/index.html#subscriptions); here's an example of the payload:

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
                "temperature",
                ]
            }
        },
        "notification": {
            "http": {
                "url": http://quantumleap:8668/notify
            },
            "attrs": [
            "temperature",
            ],
            "metadata": ["dateCreated", "dateModified"]
        },
        "throttling": 5
    }

Important thing to notice here is the presence of the ```"metadata": ["dateCreated", "dateModified"]``` part. This tells Orion to include the modification time of the attributes, and this time will be used as the time index in the database. If this is somehow missing, Quantumleap will use its current system time at which the notification arrives instead.

The notification is fed to a translator, which by default is for CrateDB as mentioned before.

In addition to the */notify* endpoint, the API will include endpoints for advanced raw and aggregated data retrieval.

The overall picture of the main pieces is shown below.

![Alt text](https://g.gravizo.com/svg?@startuml;skinparam%20componentStyle%20uml2;!define%20ICONURL%20https://raw.githubusercontent.com/smartsdk/architecture-diagrams/smartsdk-template/dist;!includeurl%20ICONURL/common.puml;!includeurl%20ICONURL/fiware.puml;!includeurl%20ICONURL/smartsdk.puml;interface%20NGSI;FIWARE%28cb,%22Context%20Broker%20\n%20-%20Orion%22,component%29;[Sensor%20@%20IoT%20Layer]%20-right-%20NGSI;NGSI%20-right-%20cb;package%20%22Quantumleap%22%20{;SMARTSDK%28api,%22API%22,component%29;SMARTSDK%28translator,%22Translator%22,component%29;api%20-up-%20NGSI;api%20-down-%20translator;};[CrateDB]%20-left-%20translator;[Grafana]%20-down-%20CrateDB;@enduml;)

## Development Setup and Structure

The development is mostly python3 based for now, and really in the early stages so things will change for sure. For now, you can start with:

    git clone https://github.com/smartsdk/ngsi-timeseries-api.git
    cd ngsi-timeseries-api
    python3 -m venv env
    pip install -r requirements.txt

    # if you want to test everything locally
    source setup_dev_env.sh

The ```requirements.txt``` still needs to be split between testing and production, that's why the docker image is massive for now.

Pytest is used as the testing framework, but since most of QL's functionality is integration of components, you'll find ```docker-compose.yml``` files in the test folders to be run as a setup for tests. If you see ```.travis.yml``` file you'll see how they are running today, but probably at some point it's worth exploring pytest-docker plugins.

In the file tree structure you can find:

- **ngsi-timeseries-api**
    - **client**: holds a simple Orion Context Broker client to ease integration testing. To be moved out of here at some point.
    - **experiments**: sandbox for quick manual tests to try some stuff and derive new test cases.
    - **python-flask** : will hold the implementation of the swagger-defined API controllers.
    - **reporter**: this module is acting as the receiver of the notifications, who "parses/validates" them before being handled to the translators.
    - **translators**: specific translators for timeseries databases.
    - **utils**: common shared stuff looking for a better place to live in.
