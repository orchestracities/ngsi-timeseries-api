from conftest import QL_URL
from reporter.tests.utils import AttrQueryResultGen, insert_test_data,\
    delete_test_data, temperatures
import pytest
import requests
import dateutil.parser
from statistics import mean


entity_id_1 = "Room1"
entity_id_2 = "Room2"
result_gen = AttrQueryResultGen(time_index_size=4,
                                entity_type='Room',
                                attr_name='temperature',
                                value_generator=temperatures)
index = result_gen.time_index()


def ix_intervals():
    bs = list(range(0, result_gen.time_index_size)) + [None]
    prod = [(i, j) for i in bs for j in bs]
    return [(i, j) for (i, j) in prod if (i is None or j is None) or (i <= j)]


def query_url(values=False):
    url = "{qlUrl}/attrs/{attrName}"
    if values:
        url += '/value'
    return url.format(
        qlUrl=QL_URL,
        attrName=result_gen.attr_name()
    )


@pytest.fixture(scope='module')
def reporter_dataset():
    service = ''
    entity_type = result_gen.formatter.entity_type
    sz = result_gen.time_index_size
    insert_test_data(service, [entity_type], n_entities=1,
                     index_size=sz, entity_id=entity_id_1)
    insert_test_data(service, [entity_type], n_entities=1,
                     index_size=sz, entity_id=entity_id_2)
    yield
    delete_test_data(service, [entity_type])


def assert_entities(response, entity_ids, ix_lo=None, ix_hi=None,
                    values_only=False):
    assert response.status_code == 200, response.text

    actual = response.json()
    assert isinstance(actual, dict)

    expected = result_gen.values(entity_ids, ix_lo, ix_hi, values_only)
    assert actual == expected


def assert_aggregate(response, entity_ids, aggregator, ix_lo=None, ix_hi=None):
    assert response.status_code == 200, response.text

    actual = response.json()
    assert isinstance(actual, dict)

    expected = result_gen.aggregate(aggregator, entity_ids, ix_lo, ix_hi)
    assert actual == expected


def test_NTNE1A_defaults(reporter_dataset):
    response = requests.get(query_url())
    assert_entities(response, [entity_id_1, entity_id_2])


def test_NTNE1A_type(reporter_dataset):
    query_params = {
        'type': result_gen.entity_type()
    }
    response = requests.get(query_url(), params=query_params)
    assert_entities(response, [entity_id_1, entity_id_2])


def test_NTNE1A_one_entity(reporter_dataset):
    query_params = {
        'id': entity_id_1
    }
    response = requests.get(query_url(), params=query_params)
    assert_entities(response, [entity_id_1])


def test_NTNENA_some_entities(reporter_dataset):
    entity_ids = "{}, {}".format(entity_id_1, entity_id_2)
    query_params = {
        'id': entity_ids
    }
    response = requests.get(query_url(), params=query_params)
    assert_entities(response, [entity_id_1, entity_id_2])


def test_NTNE1A_values_defaults(reporter_dataset):
    entity_ids = "{},{},{}".format(entity_id_1, entity_id_2, 'RoomNotValid')
    # should ignore RoomNotValid
    query_params = {
        'id': entity_ids
    }
    response = requests.get(query_url(values=True), params=query_params)
    assert_entities(response, [entity_id_1, entity_id_2], values_only=True)


def test_weird_ids(reporter_dataset):
    """
    Invalid ids are ignored (provided at least one is valid to avoid 404).
    Empty values are ignored.
    Order of ids is preserved in response (e.g., Room1 first, Room0 later)
    """
    entity_ids = "{},{},{}".format(entity_id_1, 'RoomNotValid', entity_id_2)
    query_params = {
        'id': entity_ids
    }
    response = requests.get(query_url(), params=query_params)
    assert_entities(response, [entity_id_1, entity_id_2])


@pytest.mark.parametrize('ix_lo, ix_hi', ix_intervals())
def test_NTNE1A_fromDate_toDate(reporter_dataset, ix_lo, ix_hi):
    query_params = {
        'types': 'entity_type'
    }
    if ix_lo is not None:
        query_params['fromDate'] = index[ix_lo]
    if ix_hi is not None:
        query_params['toDate'] = index[ix_hi]

    response = requests.get(query_url(), params=query_params)
    assert_entities(response, [entity_id_1, entity_id_2], ix_lo, ix_hi)


def test_NTNE1A_fromDate_toDate_with_quotes(reporter_dataset):
    query_params = {
        'types': 'entity_type',   
        'fromDate': '"{}"'.format(index[0]),
        'toDate': '"{}"'.format(index[-1])
    }
    response = requests.get(query_url(), params=query_params)
    assert_entities(response, [entity_id_1, entity_id_2])


def test_NTNE1A_limit(reporter_dataset):
    query_params = {
        'limit': 10
    }
    response = requests.get(query_url(), params=query_params)
    assert_entities(response, [entity_id_1, entity_id_2])


def test_NTNE1A_combined(reporter_dataset):
    query_params = {
        'type': result_gen.entity_type(),
        'fromDate': index[0],
        'toDate': index[2],
        'limit': 10,
    }
    response = requests.get(query_url(), params=query_params)
    assert_entities(response, [entity_id_1, entity_id_2], ix_hi=2)


@pytest.mark.parametrize("aggr_period, exp_index, ins_period", [
    ("day",    ['1970-01-01T00:00:00.000+00:00',
                '1970-01-02T00:00:00.000+00:00',
                '1970-01-03T00:00:00.000+00:00'], "hour"),
    ("hour",   ['1970-01-01T00:00:00.000+00:00',
                '1970-01-01T01:00:00.000+00:00',
                '1970-01-01T02:00:00.000+00:00'], "minute"),
    ("minute", ['1970-01-01T00:00:00.000+00:00',
                '1970-01-01T00:01:00.000+00:00',
                '1970-01-01T00:02:00.000+00:00'], "second"),
])
def test_NTNE1A_aggrPeriod(aggr_period, exp_index, ins_period):
    # Custom index to test aggrPeriod
    service = ''
    entity_type = 'test_NTNE1A_aggrPeriod'
    # The reporter_dataset fixture is still in the DB cos it has a scope of
    # module. We use a different entity type to store this test's rows in a
    # different table to avoid messing up global state---see also delete down
    # below.
    entity_id = "{}0".format(entity_type)
    attr_name = result_gen.attr_name()

    for i in exp_index:
        base = dateutil.parser.isoparse(i)
        insert_test_data(service,
                         [entity_type],
                         entity_id=entity_id,
                         index_size=5,
                         index_base=base,
                         index_period=ins_period)

    # aggrPeriod needs aggrMethod
    query_params = {
        'aggrPeriod': aggr_period,
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 400, r.text

    # Check aggregation with aggrPeriod
    query_params = {
        'type': entity_type,  # avoid picking up temperatures of entities
                              # in reporter_dataset fixture.
        'attrs': attr_name,
        'aggrMethod': 'sum',
        'aggrPeriod': aggr_period,
    }
    r = requests.get(query_url(), params=query_params)

    delete_test_data(service, [entity_type])

    assert r.status_code == 200, r.text
    expected_temperatures = 0 + 1 + 2 + 3 + 4
    # Assert
    obtained = r.json()
    expected_entities = [
        {
            'entityId': entity_id,
            'index': exp_index,
            'values': [expected_temperatures, expected_temperatures,
                       expected_temperatures]
        } 
    ]
    expected_types = [
        {
            'entities': expected_entities,
            'entityType': entity_type
        }
    ]
    expected = {
        'attrName': attr_name,
        'types': expected_types,
    }

    assert obtained == expected


def test_not_found(reporter_dataset):
    query_params = {
        'id': 'RoomNotValid'
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 404, r.text
    assert r.json() == {
        "error": "Not Found",
        "description": "No records were found for such query."
    }


def test_NTNE1A_aggrScope(reporter_dataset):
    # Notify users when not yet implemented
    query_params = {
        'aggrMethod': 'avg',
        'aggrScope': 'global',
    }
    r = requests.get(query_url(), params=query_params)
    assert r.status_code == 501, r.text


@pytest.mark.parametrize('aggr_method, aggregator, ix_lo, ix_hi',
    [('count', len, lo, hi) for (lo, hi) in ix_intervals()] +
    [('sum', sum, lo, hi) for (lo, hi) in ix_intervals()] +
    [('avg', mean, lo, hi) for (lo, hi) in ix_intervals()] +
    [('min', min, lo, hi) for (lo, hi) in ix_intervals()] +
    [('max', max, lo, hi) for (lo, hi) in ix_intervals()]
)
def test_aggregating_entities_of_same_type(reporter_dataset,
                                           aggr_method, aggregator,
                                           ix_lo, ix_hi):
    query_params = {
        'type': result_gen.entity_type(),
        'aggrMethod': aggr_method
    }
    if ix_lo is not None:
        query_params['fromDate'] = index[ix_lo]
    if ix_hi is not None:
        query_params['toDate'] = index[ix_hi]

    response = requests.get(query_url(), params=query_params)
    assert_aggregate(response, [entity_id_1, entity_id_2], aggregator,
                     ix_lo, ix_hi)


@pytest.mark.parametrize('aggr_method, aggregator, ix_lo, ix_hi',
    [('count', len, lo, hi) for (lo, hi) in ix_intervals()] +
    [('sum', sum, lo, hi) for (lo, hi) in ix_intervals()] +
    [('avg', mean, lo, hi) for (lo, hi) in ix_intervals()] +
    [('min', min, lo, hi) for (lo, hi) in ix_intervals()] +
    [('max', max, lo, hi) for (lo, hi) in ix_intervals()]
)
def test_aggregating_single_entity(reporter_dataset,
                                   aggr_method, aggregator,
                                   ix_lo, ix_hi):
    query_params = {
        'attrs': result_gen.attr_name(),
        'id': entity_id_1,
        'aggrMethod': aggr_method
    }
    if ix_lo is not None:
        query_params['fromDate'] = index[ix_lo]
    if ix_hi is not None:
        query_params['toDate'] = index[ix_hi]

    response = requests.get(query_url(), params=query_params)
    assert_aggregate(response, [entity_id_1], aggregator, ix_lo, ix_hi)
