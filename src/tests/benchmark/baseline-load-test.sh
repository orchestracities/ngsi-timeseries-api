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

docker build --cache-from orchestracities/quantumleap -t orchestracities/quantumleap ../../../

docker-compose up -d

sleep 10

# seq 1 10000 | xargs -n1 -P10  curl 'http://localhost:8668/version'
# ^ this is the slowest client, probably because of context switches and
#   lack of connection pooling.
# python asyncio_driver.py version
# ^ this is way faster as it does async I/O and pools connections, but
#   the one below beats them all!
python threaded_driver.py version

docker-compose down -v

echo '>>>'
echo '>>> Duration, GC and OS time series collected in _monitoring dir.'
echo '>>> Run "python -i analysis.py" to explore your data.'
echo '>>>'