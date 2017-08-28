# Crate

[**Crate**](https://crate.io) is QuantumLeap's default backend where NGSI data will be persisted. Until QuantumLeap implements its querying API, you can interact directly with Crate to query all the data QL has saved from the received notifications.

If you followed the [Installation Guide](./index.md), you have already Crate running in a Docker container, ready to be used.

The easiest way to interact with it is using its admin interface, as documented [here](https://crate.io/docs/crate/guide/getting_started/connect/admin_ui.html). If not, you can use its [HTTP api](https://crate.io/docs/crate/guide/getting_started/connect/rest.html), or any of its supported drivers for different programming languages.

You can learn more about Crate by reading the docs at [https://crate.io/docs/crate/reference/](https://crate.io/docs/crate/reference/).
