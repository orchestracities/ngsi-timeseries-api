#!/usr/bin/env bash

set -e

DOCKER_IMG=timescale/timescaledb-postgis:${TIMESCALE_VERSION}
PORT=5432
PASS=abc123
DATA=ql-db-init/mtutenant.etdevice.csv
DATA_LOADER=sql/import-mtutenant.etdevice-data.sql
PG_CONN_URI=postgres://postgres:$PASS@localhost:5432/
QL_CONN_URI=postgres://quantumleap:*@localhost:5432/quantumleap

# Pull Timescale+PostGIS image and start container.
docker pull $DOCKER_IMG
docker run -d \
    --name timescaledb \
    -e POSTGRES_PASSWORD=$PASS \
    -p $PORT:$PORT \
    --mount type=bind,source="$(pwd)"/$DATA,target=/mtutenant.etdevice.csv \
    --mount type=bind,source="$(pwd)"/$DATA_LOADER,target=/$DATA_LOADER \
    $DOCKER_IMG

# Give the container enough time to start up Postgres.
sleep 5

# Bootstrap QuantumLeap DB with PostGIS and Timescale extensions.
cat sql/bootstrap.sql | docker exec -i timescaledb psql $PG_CONN_URI

# Create Lusovini schema and tables.
cat ql-db-init/1-mtutenant.etdevice-ddl.sql \
    | docker exec -i timescaledb psql $QL_CONN_URI

# Load the data exported from CrateDB.
# Note this is a server-side import so you'll have to be superuser.
docker exec -i timescaledb psql $PG_CONN_URI -f /$DATA_LOADER

# Check records were imported correctly.
cat sql/count-imported-records.sql \
    | docker exec -i timescaledb psql $QL_CONN_URI

# Clean up after yourself!
# $ docker kill timescaledb
# $ docker container prune && docker volume prune
# or simply:
# $ docker kill timescaledb && docker system prune
