# Telemetry

QuantumLeap ships with a telemetry component for concurrent, low memory
footprint, efficient collection of time-varying quantities. Presently,
it is possible to collect:

* Duration of selected code blocks;
* Python garbage collection metrics;
* Python profiler (cProfile) data;
* Operating system resource usage: maximum resident set size, user and
  kernel time.

Profiler data is collected in files that can be loaded into the Python
built-in analyser (`pstats`) whereas all other sampled quantities are
assembled into time series and output to CSV files which can be easily
imported into data analysis tools such as Pandas or a time series database
such as Crate or Timescale.

## Output files

As QuantumLeap collects telemetry data, files will be written to a
monitoring directory of your choice. Duration time series are output
to CSV files having a "duration" prefix and "csv" extension. Likewise
garbage collection and operating system resource usage time series are
collected in CSV files having a prefix of "runtime" and an extension
of "csv". Finally profiler data go into files having a name of:
"profiler.PID.data" where PID is the operating system PID of the process
being profiled---e.g. "profiler.5662.data". CSV files can be read and
deleted at will without interfering with QuantumLeap's telemetry collection
process, even if QuantumLeap is restarted multiple times. On the other
hand, profiler data files should only be opened after stopping QuantumLeap.
(These files are produced by cProfile not by QuantumLeap, so it is best
not to touch them until cProfile exits.)

## Output format

The profiler data files are binary files in the cProfile format as
documented in the Python standard library, hence they will not be
discussed here. The CSV files contain time series data and fields
are arranged as follows:

* **Timepoint**: time at which the measurement was taken, expressed
    as number of nanoseconds since the epoch. (Integer value.)
* **Measurement**: sampled quantity. (Float value.)
* **Label**: name used to identify a particular kind of measurement
    when sampling. (String value.)
* **PID**: operating system ID of the process that sampled the quantity.

Out of convenience, the CSV file starts with a header of:

```csv
Timepoint, Measurement, Label, PID
```

For duration files the sampled quantity is the amount of time, in
fractional seconds, that an HTTP request took to complete and the
label identifies that request using a combination of path and verb
as shown in the duration file excerpt below

```csv
Timepoint, Measurement, Label, PID
    ...
1607092101580206000, 0.237, "/v2/notify [POST]", 5659
    ...
1607092101580275000, 0.291, "/v2/notify [POST]", 5662
    ...
```

Runtime files contain both Python garbage collection and operating
system resource usage time series. Labels and measurements are as
follows.

* **GC collections**. Each measurement in the series represents the total
    number of times the GC collector swept memory since the interpreter
    was started. (This is the total across all generations.) The series
    is labelled with "gc collections".
* **GC collected**. Each measurement in the series represents the total
    number of objects the GC collector freed since the interpreter was
    started. (This is the total across all generations.) The series is
    labelled with "gc collected".
* **GC uncollectable**. Each measurement in the series represents the
    total number of objects the GC collector couldn't free since the
    interpreter was started. (This is the total across all generations.)
    The series is labelled with "gc uncollectable".
* **User Time**. Each measurement in the series is the total amount of
    time, in seconds, the process spent executing in user mode. The
    series is labelled with "user time".
* **System Time**. Each measurement in the series is the total amount of
    time, in seconds, the process spent executing in kernel mode. The
    series is labelled with "system time".
* **Maximum RSS**. Each measurement in the series is maximum resident set
    size used. The value will be in kilobytes on Linux and bytes on MacOS.
    The series is labelled with "max rss".

## Basic usage

Telemetry is turned off by default but can easily be switched on using
the Gunicorn configuration file provided in the `server` package:
`gconfig_telemetry.py`. With this configuration, QuantumLeap will collect

* The duration of each HTTP request;
* Python garbage collection metrics;
* Operating system resource usage: maximum resident set size, user and
  kernel time.

If profiling data are needed too, edit `gconfig_telemetry.py` to enable
Python's built-in profiler (cProfile)

```python
    def post_worker_init(worker):
        ...
        monitor.start(monitoring_dir=monitoring_dir,
                      with_runtime=True,
                      with_profiler=False)
                      #            ^ set this to True
```

By default telemetry data are written to files in the `_monitoring`
directory under QuantumLeap's current working directory---if the directory
doesn't exist, it is automatically created. To choose a different location,
set the `monitoring_dir` variable in `gconfig_telemetry.py` to your liking.

### Turning telemetry on

As mentioned earlier, telemetry is turned off by default. To turn it on,
start QuantumLeap this way

```bash
$ python app.py --config server/gconfig_telemetry.py
```

or, to use your own Gunicorn instead of QuantumLeap's embedded one

```bash
$ gunicorn server.wsgi --config server/gconfig_telemetry.py
```

If you are using the Docker image, pass the telemetry configuration
as a command argument, as in the Docker Compose snippet below:

```bash
quantumleap:
    image: orchestracities/quantumleap:latest
    command: --config server/gconfig_telemetry.py
...
```

At the moment the only way to turn telemetry off is to stop QuantumLeap
and then restart it with its default configuration---i.e. `gconfig.py`.

### Analysing telemetry data

Profiler data can be analysed interactively using the Python `pstats`
module as explained in the Python standard library documentation, e.g.

```bash
$ python -m pstats profiler.5662.data
```

CSV files can be easily imported into data analysis tools such as Pandas
or a time series database such as Crate or Timescale using the `COPY FROM`
statement. For added convenience, there is a `pandas_import` module in
the `telemetry` package that you can use to import all duration and
runtime CSV files found in the monitoring directory:

```bash
$ cd ngsi-timeseries-api
$ pipenv install --dev
$ python
>>> import pandas as pd
>>> from server.telemetry.pandas_import import TelemetryDB
>>>
>>> db = TelemetryDB('/path/to/_monitoring')
```

Then you can use the `TelemetryDB` methods to populate Pandas frames
with duration and runtime data combed from the CSV files. For example
here's how to calculate requests per second statistics for the version
endpoint and plot requests per second over time

```bash
>>> get_version = db.duration().time_series('/version [GET]')
>>> rps = get_version.data().resample('1S').count()
>>> rps.describe()
...
>>> fig = rps.plot().get_figure()
>>> fig.savefig("get-version-rps.pdf")
```

For further inspiration, you can have a look at the `analysis` module
in the `tests/benchmark` directory.

## Advanced usage

Power users who need to instrument the code to investigate performance
bottlenecks can do so by decorating functions with a duration sampler
as in the example below where a `time_it` decorator is added to the
the version endpoint's handler.

```python
from server.telemetry.monitor import time_it

@time_it(label='version()')
def version():
    ...
```

It is also possible to time specific blocks of code inside functions
or methods or in the outer module's scope, please refer to the documentation
of the `monitor` module for the details.

For more advanced scenarios or for writing your own samplers, first
familiarise yourself with the `observation` module (core functionality,
it comes with numerous examples), then have a look at the samplers in
the `sampler` module to see how to write one, finally you can use the
implementation of the `monitor` module as a starting point for wiring
together the building blocks to make them fit for your use case.
