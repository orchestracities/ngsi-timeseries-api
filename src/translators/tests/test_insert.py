# To test a single translator use the -k parameter followed by either
# timescale or crate.
# See https://docs.pytest.org/en/stable/example/parametrize.html

from exceptions.exceptions import AmbiguousNGSIIdError
from translators.base_translator import BaseTranslator
from translators.sql_translator import NGSI_TEXT, NGSI_DATETIME, NGSI_STRUCTURED_VALUE
from utils.common import *
from utils.tests.common import *
from datetime import datetime, timezone

from conftest import crate_translator, timescale_translator, entity
import pytest

from exceptions.exceptions import InvalidParameterValue

translators = [
    pytest.lazy_fixture('crate_translator'),
    pytest.lazy_fixture('timescale_translator')
]


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_parameters_validation(translator):
    limit_valid = 100
    limit_none = None
    limit_invalid = -1
    limit_too_big = 1000000
    last_n_none = None
    last_n_valid = 10
    last_n_invalid = -1
    detault_limit = translator.config.default_limit()

    assert translator._get_limit(limit_valid, last_n_none) == limit_valid
    assert translator._get_limit(limit_none, last_n_none) == detault_limit
    assert translator._get_limit(limit_too_big, last_n_none) == detault_limit
    try:
        translator._get_limit(limit_invalid, last_n_none)
    except Exception as e:
        assert isinstance(e, InvalidParameterValue)
    assert translator._get_limit(limit_valid, last_n_valid) == last_n_valid
    assert translator._get_limit(limit_none, last_n_valid) == last_n_valid
    assert translator._get_limit(limit_too_big, last_n_valid) == last_n_valid
    try:
        translator._get_limit(limit_invalid, last_n_valid)
    except Exception as e:
        assert isinstance(e, InvalidParameterValue)
    try:
        translator._get_limit(limit_valid, last_n_invalid)
    except Exception as e:
        assert isinstance(e, InvalidParameterValue)
    try:
        translator._get_limit(limit_none, last_n_invalid)
    except Exception as e:
        assert isinstance(e, InvalidParameterValue)
    try:
        translator._get_limit(limit_too_big, last_n_invalid)
    except Exception as e:
        assert isinstance(e, InvalidParameterValue)
    try:
        translator._get_limit(limit_invalid, last_n_invalid)
    except Exception as e:
        assert isinstance(e, InvalidParameterValue)
    try:
        translator._parse_limit(limit_none)
    except Exception as e:
        assert isinstance(e, InvalidParameterValue)
    try:
        translator._parse_last_n(last_n_none)
    except Exception as e:
        assert isinstance(e, InvalidParameterValue)


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_ngsi_attr_to_db(translator):
    boolean = {
        'value': True
    }
    integer = {
        'value': 1
    }
    float = {
        'value': 1.1
    }
    string_number = {
        'value': '1.1'
    }
    string_not_number = {
        'value': 'false'
    }
    structured_value = {
        'value': {'structured': 1}
    }
    array = {
        'value': ['ok', 'not_ok']
    }
    datetime = {
        'value': "2018-03-20T13:26:38.722Z"
    }
    ngsi_ld_datetime = {
        'value': {
            '@value': "2018-03-20T13:26:38.722Z",
            '@type': 'DateTime'
        },
        'type': 'Property'
    }
    # number
    assert translator._ngsi_number_to_db(boolean) is None
    assert translator._ngsi_number_to_db(integer) == 1.0
    assert translator._ngsi_number_to_db(float) == 1.1
    assert translator._ngsi_number_to_db(string_number) == 1.1
    assert translator._ngsi_number_to_db(string_not_number) is None
    assert translator._ngsi_number_to_db(structured_value) is None
    assert translator._ngsi_number_to_db(array) is None
    assert translator._ngsi_number_to_db(datetime) is None
    # integer
    assert translator._ngsi_integer_to_db(boolean) is None
    assert translator._ngsi_integer_to_db(integer) == 1
    assert translator._ngsi_integer_to_db(float) == 1
    assert translator._ngsi_integer_to_db(string_number) == 1
    assert translator._ngsi_integer_to_db(string_not_number) is None
    assert translator._ngsi_integer_to_db(structured_value) is None
    assert translator._ngsi_integer_to_db(array) is None
    assert translator._ngsi_integer_to_db(datetime) is None
    # datetime
    assert translator._ngsi_datetime_to_db(boolean) is None
    assert translator._ngsi_datetime_to_db(integer) is None
    assert translator._ngsi_datetime_to_db(float) is None
    assert translator._ngsi_datetime_to_db(string_number) is None
    assert translator._ngsi_datetime_to_db(string_not_number) is None
    assert translator._ngsi_datetime_to_db(structured_value) is None
    assert translator._ngsi_datetime_to_db(array) is None
    assert translator._ngsi_datetime_to_db(
        datetime) == "2018-03-20T13:26:38.722Z"
    # boolean
    assert translator._ngsi_boolean_to_db(boolean) is True
    assert translator._ngsi_boolean_to_db(integer) is True
    assert translator._ngsi_boolean_to_db(float) is None
    assert translator._ngsi_boolean_to_db(string_number) is None
    assert translator._ngsi_boolean_to_db(string_not_number) is False
    assert translator._ngsi_boolean_to_db(structured_value) is None
    assert translator._ngsi_boolean_to_db(array) is None
    assert translator._ngsi_boolean_to_db(datetime) is None
    # text
    assert translator._ngsi_text_to_db(boolean) == "True"
    assert translator._ngsi_text_to_db(integer) == "1"
    assert translator._ngsi_text_to_db(float) == "1.1"
    assert translator._ngsi_text_to_db(string_number) == "1.1"
    assert translator._ngsi_text_to_db(string_not_number) == "false"
    assert translator._ngsi_text_to_db(structured_value) == "{'structured': 1}"
    assert translator._ngsi_text_to_db(array) == "['ok', 'not_ok']"
    assert translator._ngsi_text_to_db(datetime) == "2018-03-20T13:26:38.722Z"
    # ngsi_ld_datetime
    assert translator._ngsi_ld_datetime_to_db(boolean) is None
    assert translator._ngsi_ld_datetime_to_db(integer) is None
    assert translator._ngsi_ld_datetime_to_db(float) is None
    assert translator._ngsi_ld_datetime_to_db(string_number) is None
    assert translator._ngsi_ld_datetime_to_db(string_not_number) is None
    assert translator._ngsi_ld_datetime_to_db(structured_value) is None
    assert translator._ngsi_ld_datetime_to_db(array) is None
    assert translator._ngsi_ld_datetime_to_db(datetime) is None
    assert translator._ngsi_ld_datetime_to_db(
        ngsi_ld_datetime) == "2018-03-20T13:26:38.722Z"


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_compute_type(translator):
    boolean = {
        'value': True
    }
    integer = {
        'value': 1
    }
    float = {
        'value': 1.1
    }
    string_number = {
        'value': '1.1'
    }
    structured_value = {
        'value': {'structured': 1}
    }
    array = {
        'value': ['ok', 'not_ok']
    }
    datetime = {
        'value': "2018-03-20T13:26:38.722Z"
    }
    ngsi_ld_datetime = {
        'value': {
            '@value': "2018-03-20T13:26:38.722Z",
            '@type': 'DateTime'
        },
        'type': 'Property'
    }
    entity_id = 'test'
    entity_type = 'undefined'
    assert translator._compute_type(
        entity_id,
        entity_type,
        boolean) == translator.NGSI_TO_SQL['Boolean']
    assert translator._compute_type(
        entity_id,
        entity_type,
        integer) == translator.NGSI_TO_SQL['Integer']
    assert translator._compute_type(
        entity_id,
        entity_type,
        float) == translator.NGSI_TO_SQL['Number']
    assert translator._compute_type(
        entity_id,
        entity_type,
        string_number) == translator.NGSI_TO_SQL[NGSI_TEXT]
    assert translator._compute_type(
        entity_id,
        entity_type,
        structured_value) == translator.NGSI_TO_SQL[NGSI_STRUCTURED_VALUE]
    assert translator._compute_type(
        entity_id,
        entity_type,
        array) == translator.NGSI_TO_SQL['Array']
    assert translator._compute_type(
        entity_id,
        entity_type,
        datetime) == translator.NGSI_TO_SQL[NGSI_DATETIME]
    assert translator._compute_type(
        entity_id,
        entity_type,
        ngsi_ld_datetime) == translator.NGSI_TO_SQL[NGSI_DATETIME]


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_insert_empty_dict(translator):
    entities = dict()
    try:
        translator.insert(entities)
    except Exception as e:
        assert isinstance(e, TypeError)
    finally:
        translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_insert(translator):
    entities = create_random_entities(1, 2, 3, use_time=True, use_geo=True)
    result = translator.insert(entities)
    assert result.rowcount > 0
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_insert_entity(translator, entity):
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat(timespec='milliseconds')
    entity[BaseTranslator.TIME_INDEX_NAME] = now_iso

    result = translator.insert([entity])
    assert result.rowcount != 0

    loaded_entities, err = translator.query()
    assert len(loaded_entities) == 1

    check_notifications_record([entity], loaded_entities)
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_insert_same_entity_with_different_attrs(
        translator, sameEntityWithDifferentAttrs):
    """
    Test that the CrateTranslator can insert entity updates  that are of the same type but have different attributes.
    """
    # Add time index to the updates. Use the dateModified meta data attribute
    # of temperature.
    for entity in sameEntityWithDifferentAttrs:
        entity[BaseTranslator.TIME_INDEX_NAME] = entity['temperature']['metadata']['dateModified']['value']

    result = translator.insert(sameEntityWithDifferentAttrs)
    assert result.rowcount != 0

    loaded_entities, err = translator.query()
    assert len(loaded_entities) == 1

    check_notifications_record(sameEntityWithDifferentAttrs, loaded_entities)
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_insert_multiple_types(translator):
    args = {
        'num_types': 3,
        'num_ids_per_type': 2,
        'num_updates': 1,
        'use_time': True,
        'use_geo': True
    }
    entities = create_random_entities(**args)
    result = translator.insert(entities)
    assert result.rowcount > 0

    # Again to check metadata handling works fine
    entities = create_random_entities(**args)
    result = translator.insert(entities)
    assert result.rowcount > 0
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_query_all_before_insert(translator):
    # Query all
    loaded_entities, err = translator.query()
    assert len(loaded_entities) == 0

    # Query Some
    loaded_entities, err = translator.query(entity_type="Lamp",
                                            fiware_service="openiot",
                                            fiware_servicepath="/")
    assert len(loaded_entities) == 0

    # Query one
    loaded_entities, err = translator.query(entity_id="Lamp:001",
                                            fiware_service="openiot",
                                            fiware_servicepath="/")
    assert len(loaded_entities) == 0
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_query_all(translator):
    num_types = 2
    num_ids = 2
    num_updates = 2
    args = {
        'num_types': num_types,
        'num_ids_per_type': num_ids,
        'num_updates': num_updates,
        'use_time': True,
        'use_geo': True
    }
    entities = create_random_entities(**args)
    result = translator.insert(entities)
    assert result.rowcount > 0

    loaded_entities, err = translator.query()
    assert len(loaded_entities) == 2 * 2

    for i in ['0-0', '0-1', '1-0', '1-1']:
        notifications = [e for e in entities if e['id'] == i]
        records = [e for e in loaded_entities if e['id'] == i]
        check_notifications_record(notifications, records)
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_limit_0(translator):
    entities = create_random_entities(num_updates=2)
    result = translator.insert(entities)
    assert result.rowcount > 0

    loaded_entities, err = translator.query(last_n=0)
    assert loaded_entities == []

    loaded_entities, err = translator.query(limit=0)
    assert loaded_entities == []
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_limit_overrides_lastN(translator):
    entities = create_random_entities(num_updates=7)
    result = translator.insert(entities)
    assert result.rowcount > 0

    loaded_entities, err = translator.query(last_n=5, limit=3)
    assert len(loaded_entities[0]['index']) == 3
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_lastN_ordering(translator):
    entities = create_random_entities(num_updates=5)
    result = translator.insert(entities)
    assert result.rowcount > 0

    loaded_entities, err = translator.query(last_n=3)
    index = loaded_entities[0]['index']
    assert len(index) == 3
    assert index[-1] > index[0]
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_attrs_by_entity_id(translator):
    # First insert some data
    num_updates = 10
    entities = create_random_entities(num_types=2,
                                      num_ids_per_type=2,
                                      num_updates=num_updates,
                                      use_time=True,
                                      use_geo=True)
    translator.insert(entities)

    # Now query by entity id
    entity_id = '0-1'
    loaded_entities, err = translator.query(
        entity_type='0', entity_id=entity_id)
    notifications = [e for e in entities
                     if e['type'] == '0' and e['id'] == '0-1']
    check_notifications_record(notifications, loaded_entities)

    # entity_type should be optional
    entity_id = '1-1'
    loaded_entities, err = translator.query(entity_id=entity_id)
    notifications = [e for e in entities
                     if e['type'] == '1' and e['id'] == '1-1']
    check_notifications_record(notifications, loaded_entities)

    # nonexistent id should return no data
    loaded_entities, err = translator.query(entity_id='some_nonexistent_id')
    assert len(loaded_entities) == 0
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_attrs_by_id_ambiguity(translator):
    entities = create_random_entities(num_types=2,
                                      num_ids_per_type=1,
                                      num_updates=3)
    for e in entities:
        e['id'] = 'repeated_id'

    translator.insert(entities)

    # OK if specifying type
    loaded_entities, err = translator.query(
        entity_type='0', entity_id='repeated_id')
    assert len(loaded_entities[0]['index']) == 3
    assert len(loaded_entities) == 1

    # NOT OK otherwise
    with pytest.raises(AmbiguousNGSIIdError):
        translator.query(entity_id='repeated_id')
    translator.clean()


# TODO: This query is only for CRATE not for TIMESCALE
WITHIN_EAST_HEMISPHERE = "within(attr_geo, " \
    "'POLYGON ((0 -90, 180 -90, 180 90, 0 90, 0 -90))')"


def within_east_hemisphere(e):
    return e["attr_geo"]["values"][0]["coordinates"][0] > 0


def beyond_mid_epoch(e):
    mid_epoch = datetime(1970, 6, 28).isoformat(timespec='milliseconds')
    return e["attr_time"]["values"][0] > mid_epoch


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
@pytest.mark.parametrize("attr_name, clause, tester", [
    ("attr_bool", "= True", lambda e: e["attr_bool"]["values"][0]),
    ("attr_str", "> 'M'", lambda e: e["attr_str"]["values"][0] > "M"),
    ("attr_float", "< 0.5", lambda e: e["attr_float"]["values"][0] < 0.5),
    ("attr_time", "> '1970-06-28T00:00'", beyond_mid_epoch)
    ##    (WITHIN_EAST_HEMISPHERE, "", within_east_hemisphere)
])
def test_query_per_attribute(translator, attr_name, clause, tester):
    num_types = 1
    num_ids_per_type = 2
    num_updates = 10

    entities = create_random_entities(num_types, num_ids_per_type, num_updates,
                                      use_time=True, use_geo=True)
    translator.insert(entities)

    where_clause = "where {} {}".format(attr_name, clause)
    entities, err = translator.query(
        entity_type='0', where_clause=where_clause)

    total = num_types * num_ids_per_type * num_updates

    assert len(entities) > 0, "No entities where found " \
                              "with the clause: {}{}".format(attr_name, clause)
    assert len(entities) < total, "All entities matched the clause. " \
                                  "Not expected from an " \
                                  "uniform random distribution"
    assert all(map(tester, entities))
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_unsupported_ngsi_type(translator):
    e = {
        "type": "SoMeWeIrDtYpE",
        "id": "sOmEwEiRdId",
        TIME_INDEX_NAME: datetime.now(
            timezone.utc).isoformat(
            timespec='milliseconds'),
        "foo": {
            "type": "IgnoreThisDefinitivelyNotValidNGSITypeMessage",
                "value": "BaR",
        },
    }
    translator.insert([e])
    entities, err = translator.query()
    check_notifications_record([e], entities)
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_accept_unknown_ngsi_type(translator):
    """
    test to validate issue #129
    automatic casting to NGSI data type
    https://github.com/orchestracities/ngsi-timeseries-api/issues/129
    """
    e = {
        "type": "SoMeWeIrDtYpE",
        "id": "sOmEwEiRdId",
        TIME_INDEX_NAME: datetime.now(
            timezone.utc).isoformat(
            timespec='milliseconds'),
        "address": {
            "type": "PostalAddress",
                "value": {
                    "streetAddress": "18 Avenue Félix Faure",
                    "postalCode": "06000",
                    "addressLocality": "Nice",
                    "addressCountry": "France"},
        },
    }
    translator.insert([e])
    entities, err = translator.query()
    check_notifications_record([e], entities)
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_accept_special_chars(translator):
    """
    test to validate issue #128
    attributes names and entity type containing '-' are not accepted by crateDB
    https://github.com/orchestracities/ngsi-timeseries-api/issues/128
    """
    e = {
        "type": "SoMe-WeIrD-tYpE",
        "id": "sOmE:wEiRd.Id",
        TIME_INDEX_NAME: datetime.now(
            timezone.utc).isoformat(
            timespec='milliseconds'),
        "address": {
            "type": "Address-Type",
                "value": {
                    "streetAddress": "18 Avenue Félix Faure",
                    "postalCode": "06000",
                    "addressLocality": "Nice",
                    "addressCountry": "France"},
        },
    }
    translator.insert([e])
    entities, err = translator.query()
    check_notifications_record([e], entities)
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_missing_type_defaults_to_string(translator):
    e = {
        "type": "SoMeWeIrDtYpE",
        "id": "sOmEwEiRdId",
        TIME_INDEX_NAME: datetime.now(
            timezone.utc).isoformat(
            timespec='milliseconds'),
        "foo": {
            "value": "BaR",
        },
    }
    translator.insert([e])
    entities, err = translator.query()
    assert len(entities) == 1

    # Response will include the type
    e["foo"]["type"] = NGSI_TEXT
    check_notifications_record([e], entities)
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_capitals(translator):
    entity_type = "SoMeWeIrDtYpE"
    e1 = {
        "type": entity_type, "id": "sOmEwEiRdId", TIME_INDEX_NAME: datetime.now(
            timezone.utc).isoformat(
            timespec='milliseconds'), "Foo": {
                "type": "Text", "value": "FoO", }, "bAr": {
            "type": "Text", "value": "bAr", }, }
    translator.insert([e1])
    entities, err = translator.query()
    assert len(entities) == 1
    check_notifications_record([e1], entities)

    # If a new attribute comes later, I want it translated as well.
    e2 = e1.copy()
    e2['id'] = 'SOmEwEiRdId2'
    e2['NewAttr'] = {"type": "Text", "value": "NewAttrValue!"}
    e2[TIME_INDEX_NAME] = datetime.now(
        timezone.utc).isoformat(timespec='milliseconds')

    translator.insert([e2])
    entities, err = translator.query()
    assert len(entities) == 2

    assert entities[0]['id'] == e2['id']
    assert entities[0]['NewAttr']['values'] == [e2['NewAttr']['value']]

    # Note that old entity gets None for the new attribute
    assert entities[1]['id'] == e1['id']
    assert entities[1]['NewAttr']['values'] == [None]
    translator.clean()


@pytest.mark.filterwarnings("ignore")
@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_no_time_index(translator):
    """
    The Reporter is responsible for injecting the 'time_index' attribute to the
    entity. If for some reason there's no such index, the translator will add
    one with current_time.
    """
    e = {
        'id': 'entityId1',
        'type': 'type1',
        'foo': {'type': 'Text', 'value': "SomeText"}
    }
    translator.insert([e])
    records, err = translator.query()
    assert len(records) == 1
    assert len(records[0]['index']) == 1
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_long_json(translator):
    # Github issue 44
    big_entity = {
        'id': 'entityId1',
        'type': 'type1',
        TIME_INDEX_NAME: datetime.now(
            timezone.utc).isoformat(
            timespec='milliseconds'),
        'foo': {
            'type': 'Text',
                'value': "SomeTextThatWillGetLong" *
            2000}}
    translator.insert([big_entity])

    r, err = translator.query()
    assert len(r) == 1
    check_notifications_record([big_entity], r)
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_structured_value_to_array(translator):
    entity = {
        'id': '8906',
        'type': 'AirQualityObserved',
        TIME_INDEX_NAME: datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
        'aqi': {'type': 'Number', 'value': 43},
        'city': {'type': 'Text', 'value': 'Antwerpen'},
        'h': {'type': 'Number', 'value': 93},
        'location': {
            'type': 'geo:point',
            'value': '51.2056589, 4.4180728',
        },
        'measurand': {
            'type': 'StructuredValue',
            'value': ['pm25, 43, ugm3, PM25', 'pm10, 30, ugm3, PM10',
                      'p, 1012, hPa, Pressure']
        },
        'p': {'type': 'Number', 'value': 1012},
        'pm10': {'type': 'Number', 'value': 30},
        'pm25': {'type': 'Number', 'value': 43},
        't': {'type': 'Number', 'value': 8.33}
    }
    translator.insert([entity])

    r, err = translator.query()
    check_notifications_record([entity], r)
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_ISO8601(translator):
    """
    ISO8601 should be a valid type, equivalent to DateTime.
    """
    e = {
        "type": "MyType",
        "id": "MyId",
        TIME_INDEX_NAME: datetime.now(
            timezone.utc).isoformat(
            timespec='milliseconds'),
        "iso_attr": {
            "type": "ISO8601",
                "value": "2018-03-20T13:26:38.722Z",
        },
    }
    translator.insert([e])

    loaded, err = translator.query()
    assert len(loaded) > 0
    check_notifications_record([e], loaded)
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_query_last_value(translator):
    entities = create_random_entities(1, 2, 3, use_time=True, use_geo=True)
    result = translator.insert(entities)
    assert result.rowcount > 0
    result = translator.query_last_value()
    assert len(result) == 2
    original = entities[5]
    original_index = original.pop('time_index')
    returned = result[1]
    returned_index = returned.pop('dateModified')
    assert original == returned
    assert original_index == returned_index['value']
    translator.clean()


##########################################################################
# FIWARE DATA MODELS
##########################################################################
@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_air_quality_observed(translator, air_quality_observed):
    # Add TIME_INDEX as Reporter would
    now = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
    air_quality_observed[TIME_INDEX_NAME] = now

    translator.insert([air_quality_observed])
    loaded, err = translator.query()
    check_notifications_record([air_quality_observed], loaded)
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_traffic_flow_observed(translator, traffic_flow_observed):
    # Add TIME_INDEX as Reporter would
    now = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
    traffic_flow_observed[TIME_INDEX_NAME] = now

    translator.insert([traffic_flow_observed])
    loaded, err = translator.query()
    check_notifications_record([traffic_flow_observed], loaded)
    translator.clean()


@pytest.mark.parametrize("translator", translators, ids=["crate", "timescale"])
def test_ngsi_ld(translator, ngsi_ld):
    # Add TIME_INDEX as Reporter would
    now = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
    ngsi_ld[TIME_INDEX_NAME] = now
    # Remove @context as Reporter would
    ngsi_ld.pop('@context')

    translator.insert([ngsi_ld])
    loaded, err = translator.query()

    assert ngsi_ld['id'] == loaded[0]['id']
    assert ngsi_ld['refStreetlightModel']['object'] == loaded[0]['refStreetlightModel']['values'][0]
    assert ngsi_ld['location']['value'] == loaded[0]['location']['values'][0]

    translator.clean()
