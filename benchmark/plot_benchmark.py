from benchmark.common import *
from benchmark.test_influx import db_client as influx_client
from benchmark.test_influx import test_benchmark as influx_benchmark
from benchmark.test_crate import connection as crate_connection, cursor as crate_cursor, test_benchmark as \
    crate_benchmark
from benchmark.test_rethink import connection as rethink_connection, test_benchmark as rethink_benchmark
import numpy as np
import json


def plot_insert(results, title, labels, metrics):
    import matplotlib.pyplot as plt

    width = 1. / (1.5 * len(results))
    x_locs = np.arange(len(labels))

    fig, ax = plt.subplots()

    ax.set_ylabel('Seconds')
    ax.set_title(title)
    ax.set_xticks(x_locs - width / 2. + (len(results) * width) / 2.)
    ax.set_xticklabels(labels)

    # Plot Insert times
    tsdbs = sorted(results.keys())
    bars = []
    delta = 0.
    for tsdb in tsdbs:
        values = [results[tsdb][m] for m in metrics]
        bars.append(ax.bar(x_locs + delta, values, width))
        delta += width

    ax.legend((b[0] for b in bars), tsdbs)

    def autolabel(rects):
        """
        Attach a text label above each bar displaying its height
        """
        for rect in rects:
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width() / 2., 1.01 * height,
                    '%.3g' % height,
                    ha='center', va='bottom')

    for b in bars:
        autolabel(b)

    plt.savefig("plots/{}.png".format(title.lower()))
    plt.show()


if __name__ == '__main__':
    USE_CACHE = False
    results = {}

    # InfluxDB
    if USE_CACHE:
        with open("cache_influx.json", 'r') as f:
            influx_res = json.load(f)
    else:
        client = next(influx_client())
        influx_res = influx_benchmark(client)
        with open("cache_influx.json", 'w') as f:
            json.dump(influx_res, f)
    results["InfluxDB"] = influx_res

    # CrateDB
    if USE_CACHE:
        crate_res = None
        with open("cache_crate.json", 'r') as f:
            crate_res = json.load(f)
    else:
        conn = next(crate_connection())
        cursor = next(crate_cursor(conn))
        crate_res = crate_benchmark(cursor)
        with open("cache_crate.json", 'w') as f:
            json.dump(crate_res, f)
    results["CrateDB"] = crate_res

    # RethinkDB
    if USE_CACHE:
        rethink_res = None
        with open("cache_rethink.json", 'r') as f:
            rethink_res = json.load(f)
    else:
        conn = next(rethink_connection())
        rethink_res = rethink_benchmark(conn)
        with open("cache_rethink.json", 'w') as f:
            json.dump(rethink_res, f)
    results["RethinkDB"] = rethink_res

    plot_insert(results, title='Inserts', labels=('Insert 1', 'Insert N'), metrics=[BM_INSERT_1E, BM_INSERT_NE])

    plot_insert(results,
                title='Queries',
                labels=('Query 1A 1E', 'Query NA 1E', 'QUERY 1A NE', 'QUERY NA NE'),
                metrics=[BM_QUERY_1A1E, BM_QUERY_NA1E, BM_QUERY_1ANE, BM_QUERY_NANE])

    plot_insert(results,
                title='Aggregates',
                labels=('Aggregate 1 Entity', 'Aggregate N Entities'),
                metrics=[BM_AGGREGATE_1A1E, BM_AGGREGATE_1ANE])
