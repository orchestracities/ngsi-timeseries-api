from translators.crate import CrateTranslator
from translators.influx import InfluxTranslator
from translators.rethink import RethinkTranslator
import json
import matplotlib.pyplot as plt
import numpy as np
import os

PLOTS_DIR = "."


def plot_results(results, title, labels, metrics):
    width = 1. / (1.1 * len(results))
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
            ax.text(rect.get_x() + rect.get_width() / 2., 1.02 * height,
                    '%.3g' % height,
                    ha='center', va='bottom')

    for b in bars:
        autolabel(b)

    plt.savefig(os.path.join(PLOTS_DIR, "{}.png".format(title.lower())))
    # plt.show()


if __name__ == '__main__':
    USE_CACHE = False
    results = {}

    dbs = {
        "InfluxDB": InfluxTranslator(LOCAL),
        "CrateDB": CrateTranslator(LOCAL),
        "RethinkDB": RethinkTranslator(LOCAL),
    }

    for name, trans in dbs.items():
        filename = os.path.join(PLOTS_DIR, name + ".json")
        if USE_CACHE:
            with open(filename, 'r') as f:
                influx_res = json.load(f)
        else:
            trans.setup()
            with open(filename, 'w') as f:
                res = benchmark(trans, num_types=10, num_ids_per_type=10, num_updates=1000)
                json.dump(res, f)
                trans.dispose()
        results[name] = res

    plot_results(results, title='Inserts', labels=('Insert 1', 'Insert N'), metrics=[BM_INSERT_1E, BM_INSERT_NE])

    plot_results(results,
                 title='Queries',
                 labels=('Query 1A 1E', 'Query NA 1E', 'QUERY 1A NE', 'QUERY NA NE'),
                 metrics=[BM_QUERY_1A1E, BM_QUERY_NA1E, BM_QUERY_1ANE, BM_QUERY_NANE])

    plot_results(results,
                 title='Aggregates',
                 labels=('Aggregate 1 Entity', 'Aggregate N Entities'),
                 metrics=[BM_AGGREGATE_1A1E, BM_AGGREGATE_1ANE])
