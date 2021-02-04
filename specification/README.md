# Swagger APIs

## quantumleap.yml (WIP)

This example uses the [Connexion](https://github.com/zalando/connexion) library
on top of Flask.

To run the server for testing you can execute the following:

```bash
connexion run specification/quantumleap.yml --mock=all -v -p 8668
```

and open your browser to here:

```basj
http://0.0.0.0:8668/v2/ui/
```

Or, go to your QuantumLeap deployment to the `/v2/ui` endpoint.
