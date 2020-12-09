"""
Thread-safe, low memory footprint, and efficient collection of time-varying
quantities.

For common telemetry scenarios (timing, profiling, GC) you should just be
able to use the ``monitor`` module as is. See there for details and usage.

For more advanced scenarios or writing your own samplers, familiarise
yourself with the ``observation`` module (core functionality, comes with
lots of examples) first, then have a look at the samplers in the ``sampler``
module to see how to write one, finally you can use the implementation of
the ``monitor`` module as a starting point for wiring together the building
blocks to make them fit for your use case.
"""
