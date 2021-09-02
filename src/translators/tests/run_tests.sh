#!/usr/bin/env bash

cd ../../../

# Set test QL config file
export QL_CONFIG='src/translators/tests/ql-config.yml'

pytest src/translators/ --cov-report= --cov-config=.coveragerc --cov=src/ \
  --junitxml=test-results/junit-translators.xml
r=$?

unset QL_CONFIG

cd -

exit $r
