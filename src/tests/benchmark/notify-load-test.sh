#!/usr/bin/env bash

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

# seq 1 10000 | xargs -n1 -P10  curl 'http://localhost:8668/v2/notify' \
#  -X POST -H 'Content-Type: application/json' -d @notify-load-test.json
# ^ this is the slowest client, probably because of context switches and
#   lack of connection pooling.
# python asyncio_driver.py notify
# ^ this is way faster as it does async I/O and pools connections, but
#   the one below beats them all!
python threaded_driver.py notify

docker-compose down -v

echo '>>>'
echo '>>> Duration, GC and OS time series collected in _monitoring dir.'
echo '>>> Run "python -i analysis.py" to explore your data.'
echo '>>>'