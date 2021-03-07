#!/usr/bin/env bash

# Make sure **all** images are available before starting to test!
docker build -t orchestracities/quantumleap ../../../
docker-compose build quantumleap-db-setup
docker-compose pull crate
docker-compose pull timescale
# NOTE. The below command:
#   docker-compose pull --include-deps crate timescale
# fails on Travis for some obscure reasons which is why we're pulling
# one image at a time.

docker-compose up -d
sleep 20
docker-compose ps



cd ../../../

# Set test QL config file
export QL_CONFIG='src/translators/tests/ql-config.yml'

#pytest src/translators/ --cov-report= --cov-config=.coveragerc --cov=src/
pytest --verbose src/translators/ 
r=$?

unset QL_CONFIG

cd -

docker-compose down -v
exit $r
