#!/usr/bin/env bash
# Script to simplify local development and debugging.

export PYTHONPATH=$PWD:$PYTHONPATH

# Aliasing so that notifications from orion container reach dev localhost
LH=192.0.0.1
sudo ifconfig lo0 alias $LH

export ORION_HOST=$LH
export MONGO_HOST=$LH

export QL_URL=$LH
export CRATE_HOST=$LH
export INFLUX_HOST=$LH
export RETHINK_HOST=$LH
