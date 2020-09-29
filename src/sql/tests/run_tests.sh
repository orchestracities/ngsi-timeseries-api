#!/usr/bin/env bash

cd ../../../
pytest src/sql/ --cov-report= --cov-config=.coveragerc --cov-append --cov=src/
r=$?
cd -

exit $r
