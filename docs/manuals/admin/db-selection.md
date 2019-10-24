# Database Selection

QuantumLeap can use different time series databases to persist and
query NGSI data. Currently both [CrateDB][crate] and [Timescale][timescale]
are supported as back ends, even though query functionality is
not yet available for Timescale.

If no configuration is provided QuantumLeap assumes CrateDB is
the back end to use and will store all incoming NGSI data in it.
However, different back ends can be configured for specific tenants
through a YAML configuration file. To use this feature, you have
to set the environment variable below:

* `QL_CONFIG`: absolute pathname of the QuantumLeap YAML configuration
  file. If not set, the default configuration will be used where only
  the Crate back end is available.

The YAML configuration file specifies what back end to use for which
tenant as well as the default back end to use for any other tenant
not explicitly mentioned in the file. Here's an example YAML
configuration:

    tenants:
        t1:
            backend: Timescale
        t2:
            backend: Crate
        t3:
            backend: Timescale

    default-backend: Crate

With this configuration, any NGSI entity coming in for tenant `t1`
or `t3` will be stored in Timescale whereas tenant `t2` will use
Crate. Any tenant other than `t1`, `t2`, or `t3` gets the default
Crate back end.




[crate]: ./crate.md
    "QuantumLeap Crate"
[timescale]: ./timescale.md
    "QuantumLeap Timescale"
