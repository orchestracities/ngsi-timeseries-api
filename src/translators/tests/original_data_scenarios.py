import os
import pytest
import json
from time import sleep
from typing import Any, Callable, Generator, List

from translators.base_translator import TIME_INDEX_NAME
from translators.config import KEEP_RAW_ENTITY_VAR
from translators.sql_translator import SQLTranslator, current_timex
from translators.sql_translator import ORIGINAL_ENTITY_COL, ENTITY_ID_COL, \
    TYPE_PREFIX, TENANT_PREFIX
from utils.jsondict import maybe_value
from src.utils.tests.tenant import gen_tenant_id

ENTITY_TYPE = 'device'
TranslatorFactory = Callable[[], Generator[SQLTranslator, Any, None]]


#
# NOTE. Each test scenario gets a (sort of) unique tenant so that we won't
# have to clean up the DB after each test, which would slow down the whole
# test suite.
#


def gen_entity(entity_id: int, attr_type: str, attr_value) -> dict:
    return {
        'id': f"eid:{entity_id}",
        'type': ENTITY_TYPE,
        TIME_INDEX_NAME: current_timex(),
        'a_number': {
            'type': 'Number',
            'value': 50.12
        },
        'an_attr': {
            'type': attr_type,
            'value': attr_value
        }
    }


def assert_saved_original(actual_row, original_entity,
                          should_have_batch_id=False):
    saved_entity = actual_row[ORIGINAL_ENTITY_COL]
    data = saved_entity['data']
    if not isinstance(saved_entity['data'], dict):
        data = json.loads(data)
    assert original_entity == data
    if should_have_batch_id:
        assert saved_entity['failedBatchID']
    else:
        assert saved_entity.get('failedBatchID') is None


def assert_inserted_entity(actual_row, original_entity):
    assert actual_row['a_number'] == \
        maybe_value(original_entity, 'a_number', 'value')
    assert actual_row['an_attr'] == \
        maybe_value(original_entity, 'an_attr', 'value')
    assert actual_row[ORIGINAL_ENTITY_COL] is None


def assert_failed_entity(actual_row, original_entity):
    assert actual_row['a_number'] is None
    assert actual_row['an_attr'] is None
    assert actual_row[ORIGINAL_ENTITY_COL] is not None

    assert_saved_original(actual_row, original_entity,
                          should_have_batch_id=True)


def assert_partial_entity(actual_row, original_entity):
    assert actual_row['a_number'] == \
        maybe_value(original_entity, 'a_number', 'value')
    assert actual_row['an_attr'] != \
        maybe_value(original_entity, 'an_attr', 'value')
    assert actual_row[ORIGINAL_ENTITY_COL] is None


def full_table_name(tenant: str) -> str:
    return f'"{TENANT_PREFIX}{tenant}"."{TYPE_PREFIX}{ENTITY_TYPE}"'


class OriginalDataScenarios:

    def __init__(self, translator: TranslatorFactory, cursor,
                 delay_query_by: int = 0):
        self.translator = translator
        self.cursor = cursor
        self.delay_query_by = delay_query_by

    def get_translator(self):
        return self.translator

    def insert_entities(self, tenant: str, entities: List[dict]):
        with self.translator() as t:
            t.insert(entities, fiware_service=tenant)

    @staticmethod
    def col_name(column_description: List) -> str:
        name = column_description[0]
        if isinstance(name, bytes):
            name = name.decode('utf-8')
        return name

    def query(self, stmt: str) -> List[dict]:
        if self.delay_query_by > 0:
            sleep(self.delay_query_by)
        self.cursor.execute(stmt)
        rows = self.cursor.fetchall()

        keys = [self.col_name(k) for k in self.cursor.description]
        return [dict(zip(keys, row)) for row in rows]

    def fetch_rows(self, tenant: str) -> List[dict]:
        table = full_table_name(tenant)
        stmt = f"select * from {table} order by {ENTITY_ID_COL}"
        return self.query(stmt)

    def run_changed_attr_type_scenario(self):
        tenant = gen_tenant_id()
        good_entity = gen_entity(1, 'Number', 123)
        bad_entity = gen_entity(2, 'Text', 'shud of been a nbr!')

        self.insert_entities(tenant, [good_entity])
        self.insert_entities(tenant, [bad_entity])

        rs = self.fetch_rows(tenant)

        assert len(rs) == 2
        assert_inserted_entity(rs[0], good_entity)
        assert_failed_entity(rs[1], bad_entity)

    def run_inconsistent_attr_type_in_batch_scenario(self):
        tenant = gen_tenant_id()
        good_entity = gen_entity(1, 'Text', 'wada wada')
        bad_entity = gen_entity(2, 'DateTime', current_timex())

        self.insert_entities(tenant, [good_entity, bad_entity])

        rs = self.fetch_rows(tenant)

        assert len(rs) == 2
        assert_partial_entity(rs[0], good_entity)
        assert_partial_entity(rs[1], bad_entity)

    def run_data_loss_scenario(self):
        tenant = gen_tenant_id()
        good_entity = gen_entity(1, 'Number', 1)
        bad_entity = gen_entity(1, 'Number', 2)
        bad_entity[ORIGINAL_ENTITY_COL] = 'kaboom!'

        self.insert_entities(tenant, [good_entity])
        with pytest.raises(ValueError):
            self.insert_entities(tenant, [bad_entity])

        rs = self.fetch_rows(tenant)

        assert len(rs) == 1
        assert_inserted_entity(rs[0], good_entity)

    def run_success_scenario(self):
        tenant = gen_tenant_id()
        e1, e2, e3 = [gen_entity(k + 1, 'Number', k + 1) for k in range(3)]

        self.insert_entities(tenant, [e1])
        self.insert_entities(tenant, [e2, e3])

        rs = self.fetch_rows(tenant)

        assert len(rs) == 3
        assert_inserted_entity(rs[0], e1)
        assert_inserted_entity(rs[1], e2)
        assert_inserted_entity(rs[2], e3)

    def _do_success_scenario_with_keep_raw_on(self):
        tenant = gen_tenant_id()
        e1, e2, e3 = [gen_entity(k + 1, 'Number', k + 1) for k in range(3)]

        self.insert_entities(tenant, [e1])
        self.insert_entities(tenant, [e2, e3])

        rs = self.fetch_rows(tenant)

        assert len(rs) == 3
        assert_saved_original(rs[0], e1)
        assert_saved_original(rs[1], e2)
        assert_saved_original(rs[2], e3)

    def run_success_scenario_with_keep_raw_on(self):
        os.environ[KEEP_RAW_ENTITY_VAR] = 'true'
        try:
            self._do_success_scenario_with_keep_raw_on()
        except Exception:
            del os.environ[KEEP_RAW_ENTITY_VAR]
            raise
        del os.environ[KEEP_RAW_ENTITY_VAR]

    def query_failed_inserts(self, tenant: str,
                             fetch_batch_id_clause: str) -> List[dict]:
        table = full_table_name(tenant)
        stmt = f"select {fetch_batch_id_clause} as batch, count(*) as count" + \
            f" from {table} where {fetch_batch_id_clause} is not null" + \
            f" group by {fetch_batch_id_clause}"
        return self.query(stmt)

    def run_query_failed_entities_scenario(self, fetch_batch_id_clause: str):
        tenant = gen_tenant_id()
        good_entities = [gen_entity(k + 1, 'Number', 123) for k in range(2)]
        bad_entities = [gen_entity(k + 1, 'Text', 'shud of been a nbr!')
                        for k in range(3)]

        self.insert_entities(tenant, [good_entities[0]])
        self.insert_entities(tenant, [bad_entities[0]])
        self.insert_entities(tenant, [good_entities[1]])
        self.insert_entities(tenant, [bad_entities[1], bad_entities[2]])

        rs = self.query_failed_inserts(tenant, fetch_batch_id_clause)

        assert len(rs) == 2
        assert rs[0]['batch']
        assert rs[1]['batch']

        counts = sorted([rs[0]['count'], rs[1]['count']])
        assert counts == [1, 2]
