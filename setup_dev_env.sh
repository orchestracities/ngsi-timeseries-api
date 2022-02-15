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
    LH=`ip addr | grep docker0 | grep inet | awk '{print $2}' | cut -d"/" -f1`
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

case $(uname -m) in
    arm64)
      echo "arm64 detected set DOCKER_DEFAULT_PLATFORM=linux/amd64"
      export DOCKER_DEFAULT_PLATFORM=linux/amd64
      ;;
    i386)
      ;;
    i686)
      ;;
    x86_64)
      ;;
    arm)
      dpkg --print-architecture | grep -q "arm64" && export DOCKER_DEFAULT_PLATFORM=linux/amd64 || architecture="arm"
     ;;
esac

echo "used ip: $LH"

[[ "$PIPENV_SHELL" == "no" ]] || pipenv shell
