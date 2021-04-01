"""
Partitioning Experiment
-----------------------

Test different partitioning options and optimize for the common case. But, which is the common case?

The typical use-case scenario for QL is providing fast historical data retrieval for NGSI data gathered from sensors.
Querying typically involves more data processing than inserting does, so querying is what we want to do fast.

NGSI entities are uniquely identified by entity_type and entity_id. The types of historical queries we could have are...

| Entity Type | Entity Id | Observation  |
| ----------- | --------- | -----------  |
|      1      |     N     | Very common  |
|      1      |     1     | Common       |
|      N      |     N     | Uncommon     |
|      N      |     1     | Very uncommon|

Typically, each entity type has a predefined set of attributes. Therefore, we decided to have one table per entity type
to avoid the overhead of dynamic columns.

This test tries to answer which of the following partitioning scenarios is better for the most common use cases.

| Scenario | Partition by | Cluster by |
| -------- | ------------ | ---------- |
|     1    |    month     |  entity_id |
|     2    |  entity_id   |    month   |


Environment
-----------

To test these, we setup a 3-nodes swarm cluster with a 3-nodes Crate cluster with the recipe found at
https://github.com/smartsdk/smartsdk-recipes/tree/master/recipes/data-management/quantumleap

Make sure to setup variable CRATE_URL to the URL of your Crate Cluster.
You can also try different values for the INPUT variables.

Run this file with python3 with quantumleap's environment active (see requirements.txt in the project root).
"""
from crate import client
from datetime import datetime
import functools
import random
import sys
import time

# INPUT
CRATE_URL = "crate.mydomain.com"
SLEEP = 5  # To allow cluster to catch up
N_ENTRIES = 100
N_ENTITIES = 10

# KEYS
WM = "WITHIN MONTH"
AM = "ACROSS MONTH"
VC = "VERY COMMON"
C = "COMMON"


def random_entries(batch):
    entities = []
    for _ in range(batch):
        time_index = datetime(
            random.choice((2016, 2017)),
            random.choice(range(1, 13)),
            random.choice(range(1, 29)),
            random.choice(range(24)),
            0, 0)
        entities.append((
            'Room',
            'room {}'.format(random.choice(range(N_ENTITIES))),
            random.uniform(0, 50),
            random.uniform(700, 1400),
            time_index.isoformat()
        ))
    return entities


def create_table(cursor, table_name, clustered_by, partitioned_by):
    stmt = "create table {} (" \
        "    entity_type string, " \
        "    entity_id string, " \
        "    temperature double, " \
        "    pressure double, " \
        "    time_index timestamp, " \
        "    month timestamp GENERATED ALWAYS AS date_trunc('month', time_index)) " \
        "clustered by ({})" \
        "partitioned by ({})".format(
            table_name, clustered_by, partitioned_by)
    cursor.execute(stmt)


def insert_records(cursor, table_name):
    col_names = ['entity_type', 'entity_id',
                 'temperature', 'pressure', 'time_index']
    stmt = "insert into {} ({}) values ({})".format(
        table_name,
        ', '.join(col_names),
        ('?,' * len(col_names))[:-1]
    )
    for i in range(10):
        cursor.executemany(stmt, random_entries(N_ENTRIES // 10))
        cursor.execute("refresh table {}".format(table_name))


def query(cursor, table_name, extra_clause=''):
    res = {}

    # Within Month
    stmt = "select entity_id, avg(temperature) from {} where time_index > '{}' {} group by entity_id".format(
        table_name,
        "2017-12-01T00:00",
        extra_clause,
    )
    cursor.execute(stmt)
    res[WM] = cursor.duration

    # Across Months
    stmt = "select month, avg(pressure) from {} where time_index > '{}' {} group by month".format(
        table_name,
        "2016-06-01T00:00",
        extra_clause,
    )
    cursor.execute(stmt)
    res[AM] = cursor.duration

    return res


def cleanup(cursor, table_name):
    stmt = "drop table {}".format(table_name)
    cursor.execute(stmt)


def check_scenario(create_table):
    res = {}
    with client.connect([CRATE_URL], error_trace=True) as conn:
        cursor = conn.cursor()

        table_name = "etroom"
        create_table(cursor, table_name)

        try:
            insert_records(cursor, table_name)
            time.sleep(SLEEP)

            # Very Common
            res[VC] = query(cursor, table_name)

            # Common
            res[C] = query(cursor, table_name,
                           extra_clause="AND entity_id = 'room 0'")

        finally:
            cleanup(cursor, table_name)
    return res


def dump_test_results(f=sys.stdout):
    # Print Header
    print("SCENARIO 1: partition 'month', cluster 'entity_id'", file=f)
    print("SCENARIO 2: partition 'entity_id', cluster 'month'", file=f)
    print("*" * 50, file=f)
    print("* SLEEP TIME: {}".format(SLEEP), file=f)
    print("* N_ENTITIES: {}".format(N_ENTITIES), file=f)
    print("* N_ENTRIES: {}".format(N_ENTRIES), file=f)
    print("*" * 50, file=f)

    # Gather data
    res_sc1 = check_scenario(functools.partial(
        create_table, clustered_by='entity_id', partitioned_by='month'))
    time.sleep(SLEEP)
    res_sc2 = check_scenario(functools.partial(
        create_table, clustered_by='month', partitioned_by='entity_id'))

    # Print Results
    def print_results(T):
        print("{} Queries in [ms] \t".format(T), file=f)
        print("+" + "-" * 48 + "+", file=f)
        print("| QUERY SCOPE\t | SCENARIO 1\t| SCENARIO 2\t |", file=f)
        print("+" + "-" * 48 + "+", file=f)
        print("| {}\t | {}\t| {}\t |".format(WM, res_sc1[T][WM], res_sc2[T][WM]), file=f)
        print("+" + "-" * 48 + "+", file=f)
        print("| {}\t | {}\t| {}\t |".format(AM, res_sc1[T][AM], res_sc2[T][AM]), file=f)
        print("+" + "-" * 48 + "+", file=f)

    print_results(VC)
    print_results(C)


def test_scenarios():
    for i in range(3):
        filename = "test_{}_{}_{}_n{}.txt".format(
            SLEEP, N_ENTITIES, N_ENTRIES, i
        )
        with open(filename, "w") as f:
            dump_test_results(f)


if __name__ == '__main__':
    test_scenarios()
