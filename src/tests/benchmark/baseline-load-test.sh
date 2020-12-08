#!/usr/bin/env bash

#
# Before running this test add the time_it decorator to the version endpoint:
#
#    from server.telemetry.monitor import time_it
#
#    @time_it(label='version()')
#    def version():
#      ...
#
# After running this test load analysis.py into the Python interpreter
# to import the telemetry data collected in the _monitoring dir and
# start an interactive data analysis session with Pandas, e.g.
#
# python -i analysis.py
# >>> print_measurements_summaries(db.duration())
# ...
#
# Have a look at the examples in analysis.py for inspiration...
#

mkdir -p _monitoring
rm _monitoring/*

docker build --cache-from smartsdk/quantumleap -t smartsdk/quantumleap ../../../

docker-compose up -d

sleep 10

seq 1 10000 | xargs -n1 -P10  curl 'http://localhost:8668/version'

docker-compose down -v

echo '>>>'
echo '>>> Duration, GC and OS time series collected in _monitoring dir.'
echo '>>> Run "python -i analysis.py" to explore your data.'
echo '>>>'