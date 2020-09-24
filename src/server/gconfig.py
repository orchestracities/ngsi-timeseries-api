#
# Gunicorn settings to run QuantumLeap.
# To make configuration more manageable, we keep all our Gunicorn settings
# in this file and start Gunincorn from the Docker container without any
# command line args except for the app module and the path to this config
# file, e.g.
#
#     gunicorn server.wsgi --config server/gconfig.py
#
# Settings spec:
# - https://docs.gunicorn.org/en/stable/settings.html
#

import multiprocessing

import server


#
# Server config section.
#

bind = f"{server.DEFAULT_HOST}:{server.DEFAULT_PORT}"


#
# Worker processes config section.
# Read: https://docs.gunicorn.org/en/latest/design.html
#


# Number of worker processes for handling requests.
# We set it to the max Gunicorn recommends.
workers = multiprocessing.cpu_count() * 4 + 1

# QuantumLeap does alot of network IO, so we configure worker processes
# to use multi-threading (`gthread`) to improve performance. With this
# setting, each request gets handled in its own thread taken from a
# thread pool.
# In our tests, the `gthread` worker type had better throughput and
# latency than `gevent` but `gevent` used up less memory, most likely
# because of the difference in actual OS threads. So for now we go with
# `gthread` and a low number of threads. This has the advantage of better
# performance, reasonable memory consumption, and keeps us from accidentally
# falling into the `gevent` monkey patching rabbit hole. Also notice that
# according to Gunicorn docs, when using `gevent`, Psycopg (Timescale
# driver) needs psycogreen properly configured to take full advantage
# of async IO. (Not sure what to do for the Crate driver!)
worker_class = 'gthread'

# The size of each process's thread pool.
# So here's the surprise. In our tests, w/r/t to throughput `gthread`
# outperformed `gevent`---27% better. Latency was pretty much the same
# though. But the funny thing is that we used exactly the same number
# of worker processes and the default number of threads per process,
# which is, wait for it, 1. Yes, 1.
#
# TODO: proper benchmarking.
# We did some initial quick & dirty benchmarking to get these results.
# We'll likely have to measure better and also understand better the
# way the various Gunicorn worker types actually work. (Pun intended.)
threads = 1


#
# Logging config section.
#

loglevel = 'error'


# TODO: other settings.
# Review gunicorn default settings with an eye on security and performance.
# We might need to set more options than the above.
