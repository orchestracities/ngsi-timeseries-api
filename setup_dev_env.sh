#!/usr/bin/env bash
# Script to simplify local development and debugging. 
# Usage: 
#      $ source setup_dev_env.sh

# stop at the first command that returns a non-zero exit code.
set -e

export PYTHONPATH=${PWD}/src:${PYTHONPATH}

source deps.env

if ! command -v /sbin/ifconfig &> /dev/null
then
    LH=`( ip address show docker0 | grep 'inet' | cut -d: -f2 | awk '{ print $1}' ) 2> /dev/null`
    echo $LH
else
  LH=`( /sbin/ifconfig ens4 | grep 'inet' | cut -d: -f2 | awk '{ print $1}' ) 2> /dev/null`
  if [ -z "$LH" ]
  then
      # Aliasing so that notifications from orion container reach dev localhost
      LH=192.0.0.1
      sudo ifconfig lo0 alias $LH
  fi
fi

export ORION_HOST=$LH
export MONGO_HOST=$LH

export QL_HOST=$LH
export CRATE_HOST=$LH
export POSTGRES_HOST=$LH

export REDIS_HOST=$LH

[[ "$SHELL" == "no" ]] || pipenv shell
