#!/usr/bin/env bash

export PYTHONPATH=${PWD}/src:${PYTHONPATH}

docker build -t quantumleap .

source deps.env

LH=localhost

export ORION_HOST=$LH
export MONGO_HOST=$LH

export QL_HOST=$LH
export CRATE_HOST=$LH
export POSTGRES_HOST=$LH
export INFLUX_HOST=$LH
export RETHINK_HOST=$LH

export REDIS_HOST=$LH
