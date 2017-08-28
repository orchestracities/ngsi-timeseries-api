# Crate

[**Crate**](https://crate.io) is QuantumLeap's default backend where NGSI data will be persisted. Until QuantumLeap implements its querying API, you can interact directly with Crate to query all the data QuantumLeap has stored from the received notifications.

If you followed the [Installation Guide](./index.md), you have a ready-to-use Crate instance running in a Docker container.

The easiest way to interact with Crate is using its admin interface, as documented [here](https://crate.io/docs/crate/guide/getting_started/connect/admin_ui.html). Alternatively, you can use its [HTTP api](https://crate.io/docs/crate/guide/getting_started/connect/rest.html), or any of its [supported clients](https://crate.io/docs/crate/guide/getting_started/clients/index.html).

You can learn more about Crate by reading [the docs](https://crate.io/docs/crate/reference/).
