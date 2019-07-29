#!/usr/bin/env bash

# call with schema name: ./export-mtutenant-data mtsometesttenant

set -e

DATA_FILE=../ql-db-init/mtutenant.etdevice.csv

pipenv install

echo "Exporting test data to data file $DATA_FILE"

# NOTE In the below command, crash uses the default host and port, which
# means it'll try connecting to localhost:4200. To fetch data from prod,
# you'll have to set up K8s port forwarding before hand, e.g.
#
#     kubectl -n prod port-forward crate-0 4200
#
pipenv run crash --format csv -c "
SELECT
    accumulatedprecipitationlevel24,
    airhumidity,
    airpressure,
    airtemperature,
    batterylevel,
    entity_id,
    entity_type,
    fiware_servicepath,
    latitude,
    leafweatness,
    location,
    format('POINT (%s %s)', location_centroid[1], location_centroid[2]) AS location_centroid,
    longitude,
    manufacturername,
    precipitationlevel,
    previousprecipitationlevel,
    soilmoisture450,
    soilmoisture800,
    soiltemperature,
    solarradiation,
    date_format(time_index) AS time_index,
    date_format(timeinstant) AS timeinstant,
    winddirection,
    windspeed
FROM $1.etdevice
LIMIT 10;
" \
    | sed -e '$ d' > "$DATA_FILE"

# NOTE The sed script gets rid of the extra empty line at the end of
# crash's output that makes the Postgres CSV importer choke.
