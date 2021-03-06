#!/usr/bin/env bash
# Script to simplify local development and debugging. 
# Usage: 
#      $ source setup_dev_env.sh

# stop at the first command that returns a non-zero exit code.
set -e

export PYTHONPATH=${PWD}/src:${PYTHONPATH}

docker build -t orchestracities/quantumleap .


echo "build"

source deps.env


echo "source"

LH=`( /sbin/ifconfig ens4 | grep 'inet' | cut -d: -f2 | awk '{ print $1}' ) 2> /dev/null`
echo "lh"
echo $LH
if [ -z "$LH" ]
then
    # Aliasing so that notifications from orion container reach dev localhost
    LH=192.0.0.1
    sudo ifconfig lo0 alias $LH
fi
echo "export"
echo $LH

export ORION_HOST=$LH
export MONGO_HOST=$LH

export QL_HOST=$LH
export CRATE_HOST=$LH
export POSTGRES_HOST=$LH

export REDIS_HOST=$LH

echo "complete!"

[[ "$LH" != "192.0.0.1" ]] || pipenv shell
