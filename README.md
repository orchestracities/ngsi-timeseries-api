# QuantumLeap

[![FIWARE Core Context Management](https://nexus.lab.fiware.org/static/badges/chapters/core.svg)](https://www.fiware.org/developers/catalogue/)
[![License: MIT](https://img.shields.io/github/license/smartsdk/ngsi-timeseries-api.svg)](https://opensource.org/licenses/MIT)
[![Docker Status](https://img.shields.io/docker/pulls/smartsdk/quantumleap.svg)](https://hub.docker.com/r/smartsdk/quantumleap/)
[![Support](https://img.shields.io/badge/support-ask-yellowgreen.svg)](https://ask.fiware.org/questions/)
<br/>
[![Documentation badge](https://img.shields.io/readthedocs/quantumleap.svg)](https://quantumleap.readthedocs.io/en/latest/)
[![Build Status](https://travis-ci.com/smartsdk/ngsi-timeseries-api.svg?branch=master)](https://travis-ci.com/smartsdk/ngsi-timeseries-api)
[![Coverage Status](https://coveralls.io/repos/github/smartsdk/ngsi-timeseries-api/badge.svg?branch=master)](https://coveralls.io/github/smartsdk/ngsi-timeseries-api?branch=master)
![Status](https://nexus.lab.fiware.org/static/badges/statuses/quantum-leap.svg)
[![Swagger Validator](https://img.shields.io/swagger/valid/2.0/https/raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/json/petstore-expanded.json.svg)](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb)
[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/4394/badge)](https://bestpractices.coreinfrastructure.org/projects/4394)

QuantumLeap is the first implementation of [an API](https://app.swaggerhub.com/apis/smartsdk/ngsi-tsdb)
that supports the storage of [FIWARE NGSIv2](https://fiware.github.io/specifications/ngsiv2/stable/)
data into a [time series database](https://en.wikipedia.org/wiki/Time_series_database).
It currently also experimentally supports the injection of
[NGSI-LD](https://www.etsi.org/deliver/etsi_gs/CIM/001_099/009/01.01.01_60/gs_CIM009v010101p.pdf) in 
a backward compatible way with NGSI-v2 API. I.e. you can retrieve NGSI-LD stored data via NGSI v2
API and retrieve data will be describe following NGSI v2 format.

QuantumLeap is not a [real time](https://en.wikipedia.org/wiki/Real-time_computing)
API, its purpose is to process notifications received from the Context Broker
and to create temporal records for them. In general, the whole FIWARE stack,
being based on a micro-service architecture, cannot be regarded as real time
in case you have requirements on guaranteed delivery in a given amount of time.

However, even though hard real time may not be FIWARE's forte, in our experience
a properly tuned FIWARE stack can perform extremely well and
handle very demanding IoT workloads without a glitch - you just need to
configure your infrastructure to handle that :)

Want to know more? Refer to the [docs](https://quantumleap.readthedocs.io/en/latest/)
or checkout the Extra Resources below.

This project is part of [FIWARE](https://www.fiware.org). You can find more
FIWARE components in the [FIWARE catalogue](https://catalogue.fiware.org).

|  :books: [Documentation](https://quantumleap.rtfd.io/) | :mortar_board: [Academy](https://fiware-academy.readthedocs.io/en/latest/core/quantum-leap) |  :whale: [Docker Hub](https://hub.docker.com/r/smartsdk/quantumleap/) | :dart: [Roadmap](https://github.com/smartsdk/ngsi-timeseries-api/blob/master/docs/roadmap.md) |
|---|---|---|---|

## Contents

-   [Install](#install)
-   [Usage](#usage)
-   [Troubleshooting](#troubleshooting)
-   [Contributing](#contributing)
-   [Extra resources](#extra-resources)
-   [License](#license)

## Install

Refer to the [Installation Guide](https://quantumleap.readthedocs.io/en/latest/admin/).

QuantumLeap supports both Crate DB and Timescale as time-series DB
backends but please bear in mind that at the moment we only support
the following versions:

* Crate backend: Crate DB version `3.3.*` (will be deprecated from QL `0.9` version) and `4.*`
* Timescale backend: Postgres version `10.*` or `11.*` +
  Timescale extension `1.3.*` + Postgis extension `2.5.*`.
  
PR #373 introduced basic support for NGSI-LD. In short this means that using
the current endpoint you are able to store NGSI-LD payloads with few caveats (see #398)

## Usage

Refer to the [User Manual](https://quantumleap.readthedocs.io/en/latest/user/).

## Troubleshooting

Refer to the [Troubleshooting](https://quantumleap.readthedocs.io/en/latest/user/troubleshooting/)
section.

## Contributing

Refer to the [Contributing](https://quantumleap.readthedocs.io/en/latest/user/contributing/)
section and to the [contribution guidelines](./CONTRIBUTING.md).

## Extra resources

The following is a collection of external guides and pages where you may find
additional documentation about QuantumLeap. Note that these guides could be
outdated (so could the official docs!), so we appreciate all efforts to keep
consistency.

- [SmartSDK Guided-tour](https://guided-tour-smartsdk.readthedocs.io/en/latest/)
- [FIWARE Step-by-step](https://fiware-tutorials.readthedocs.io/en/latest/time-series-data/index.html)
- [SmartSDK Recipes](https://smartsdk-recipes.readthedocs.io/en/latest/data-management/quantumleap/readme/)
- [Orchestra Cities Helm Charts](https://github.com/orchestracities/charts)

---

## License

QuantumLeap is licensed under the [MIT](LICENSE) License

© 2017-2020 Martel Innovate
