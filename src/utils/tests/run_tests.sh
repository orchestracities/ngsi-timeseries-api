#!/usr/bin/env bash

docker build -t quantumleap ../../../

docker run -ti --rm quantumleap pytest utils/tests

exit $?
