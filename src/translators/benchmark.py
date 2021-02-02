from functools import partial
import time
import timeit

# Benchmarking metrics. A:Attribute, E:Entity
BM_INSERT_1E = "insert_1E"
BM_INSERT_NE = "insert_NE"
BM_QUERY_1A1E = "query_1A1E"
BM_QUERY_NA1E = "query_NA1E"
BM_QUERY_1ANE = "query_1ANE"
BM_QUERY_NANE = "query_NANE"
BM_AGGREGATE_1A1E = "aggregate_1A1E"
BM_AGGREGATE_1ANE = "aggregate_1ANE"


def benchmark(translator, num_types=10, num_ids_per_type=10, num_updates=10, use_time=False, use_geo=False):
    from utils.tests.common import create_random_entities, pick_random_entity_id

    results = {}
    entities = create_random_entities(num_types, num_ids_per_type, num_updates, use_time=use_time, use_geo=use_geo)

    # Insert 1 entity
    res = timeit.timeit(partial(translator.insert, entities=entities[:1]), number=1, globals=globals())
    results[BM_INSERT_1E] = res

    # Insert N entities
    n = min(1000, num_types * num_ids_per_type * num_updates//10)
    res = timeit.timeit(partial(translator.insert, entities=entities[1:n]), number=1, globals=globals())
    results[BM_INSERT_NE] = res

    # Insert the rest to have data to query
    translator.insert(entities=entities[n:])

    time.sleep(1)

    random_id = pick_random_entity_id(num_types, num_ids_per_type)
    entity_type = random_id[0]

    # Query 1 attr of 1 entity
    res = timeit.timeit(partial(translator.query, attr_names=['attr_str'], entity_type=entity_type, entity_id=random_id),
                        number=1, globals=globals())
    results[BM_QUERY_1A1E] = res

    # Query all attrs of 1 entity
    res = timeit.timeit(partial(translator.query, entity_type=entity_type, entity_id=random_id), number=1, globals=globals())
    results[BM_QUERY_NA1E] = res

    # Query 1 attr of N entities
    res = timeit.timeit(partial(translator.query, attr_names=['attr_str']), number=1, globals=globals())
    results[BM_QUERY_1ANE] = res

    # Query all attrs of N entities
    res = timeit.timeit(partial(translator.query), number=1, globals=globals())
    results[BM_QUERY_NANE] = res

    # Query aggregate on 1 entity (Needs multiple inserts for the same entity)
    res = timeit.timeit(partial(translator.average, attr_name="attr_float", entity_type=entity_type, entity_id=random_id),
                        number=1, globals=globals())
    results[BM_AGGREGATE_1A1E] = res

    # Query aggregate on all entities
    res = timeit.timeit(partial(translator.average, attr_name="attr_float"), number=1, globals=globals())
    results[BM_AGGREGATE_1ANE] = res

    return results
