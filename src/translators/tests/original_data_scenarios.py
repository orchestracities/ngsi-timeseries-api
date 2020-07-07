import json
import pytest
import random
from time import sleep
from typing import Any, Callable, Generator, List

from translators.base_translator import TIME_INDEX_NAME
from translators.sql_translator import SQLTranslator, current_timex
from translators.sql_translator import ORIGINAL_ENTITY_COL, ENTITY_ID_COL, \
    TYPE_PREFIX, TENANT_PREFIX
from utils.jsondict import maybe_value


ENTITY_TYPE = 'device'
TranslatorFactory = Callable[[], Generator[SQLTranslator, Any, None]]

#
# NOTE. Each test scenario gets a (sort of) unique tenant so that we won't
# have to clean up the DB after each test, which would slow down the whole
# test suite.
#


def gen_tenant_id() -> str:
    tid = random.randint(1, 2**32)
    return f"tenant{tid}"


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

    saved_entity = json.loads(actual_row[ORIGINAL_ENTITY_COL])
    assert original_entity == saved_entity


def full_table_name(tenant: str) -> str:
    return f'"{TENANT_PREFIX}{tenant}"."{TYPE_PREFIX}{ENTITY_TYPE}"'


class OriginalDataScenarios:

    def __init__(self, translator: TranslatorFactory, cursor,
                 delay_query_by: int = 0):
        self.translator = translator
        self.cursor = cursor
        self.delay_query_by = delay_query_by

    def insert_entities(self, tenant: str, entities: List[dict]):
        with self.translator() as t:
            t.insert(entities, fiware_service=tenant)

    @staticmethod
    def col_name(column_description: List) -> str:
        name = column_description[0]
        if isinstance(name, bytes):
            name = name.decode('utf-8')
        return name

    def fetch_rows(self, tenant: str) -> List[dict]:
        table = full_table_name(tenant)
        stmt = f"select * from {table} order by {ENTITY_ID_COL}"

        if self.delay_query_by > 0:
            sleep(self.delay_query_by)
        self.cursor.execute(stmt)
        rows = self.cursor.fetchall()

        keys = [self.col_name(k) for k in self.cursor.description]
        return [dict(zip(keys, row)) for row in rows]

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
        assert_failed_entity(rs[0], good_entity)
        assert_failed_entity(rs[1], bad_entity)

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
