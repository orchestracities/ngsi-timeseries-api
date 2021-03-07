# CrateDB Shell

> Crash is an interactive CLI tool for working with CrateDB.

## Install

Crash needs Python 3, use the Pipfile in this directory to set up a
Python 3 virtual env with Crash in it:

```bash
pipenv install
```

## Run

Set up K8s port forwarding so you can make Crash connect to prod without
going through AWS load balancer/Gravitee/Keycloak. First figure out which
pod to forward to:

```bash
kubectl -n prod get pods
```

Then set up port forwarding:

```bash
kubectl -n prod port-forward crate-0 4200
```

Now enter the virtual env and run Crash:

```bash
pipenv shell
crash
```

Crash should connect to port 4200 on localhost by default, so now you
should have a DB CLI connected to prod. Or you can just use it to run
DB commands from the shell. For example here's how to export data from
a table to a CSV file:

```bash
crash --format csv -c 'select * from mtutenant.etdevice limit 10' > t.csv
```
