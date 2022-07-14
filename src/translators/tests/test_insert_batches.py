from itertools import takewhile
import os
import pytest
import sys

from translators.base_translator import TIME_INDEX_NAME
from translators.insert_splitter import INSERT_MAX_SIZE_VAR
from translators.tests.original_data_scenarios import full_table_name, \
    gen_entity, OriginalDataScenarios
from translators.tests.test_original_data import translators, \
    with_crate, with_timescale
from src.utils.tests.tenant import gen_tenant_id
# NOTE. ^ your IDE is likely to tell you this is dead code, but it isn't
# actually, we need to bring those two fixtures into scope to use them
# with the lazy_fixture calls in 'translators'.


def set_insert_max_size(number_of_bytes: int):
    os.environ[INSERT_MAX_SIZE_VAR] = f"{number_of_bytes}B"


def clear_insert_max_size():
    os.environ[INSERT_MAX_SIZE_VAR] = ''


class DataGen:

    def __init__(self, insert_max_size: int, min_batches: int):
        self.insert_max_size = insert_max_size
        self.min_batches = min_batches
        self.unique_tenant_id = gen_tenant_id()

    @staticmethod
    def _compute_insert_vector_size_lower_bound(entity: dict) -> int:
        vs = entity['id'], entity['type'], entity[TIME_INDEX_NAME], \
            entity['a_number']['value'], entity['an_attr']['value']
        sz = [sys.getsizeof(v) for v in vs]
        return sum(sz)
    # NOTE. lower bound since it doesn't include e.g. fiware service.

    def _next_entity(self) -> (dict, int):
        eid = 0
        size = 0
        while True:
            eid += 1
            e = gen_entity(entity_id=eid, attr_type='Number', attr_value=1)
            size += self._compute_insert_vector_size_lower_bound(e)
            yield e, size

    def generate_insert_payload(self) -> [dict]:
        """
        Generate enough data that when the SQL translator is configured with
        the given insert_max_size value, it'll have to split the payload in
        at least min_batches.

        :return: the entities to insert.
        """
        sz = self.insert_max_size * self.min_batches
        ts = takewhile(lambda t: t[1] <= sz, self._next_entity())
        return [t[0] for t in ts]
# NOTE. Actual number of batches >= min_batches.
# In fact, say each entity row vector is actually 10 bytes, but our computed
# lower bound is 5. Then with insert_max_size=10 and min_batches=3, es will
# have 6 entities in it for a total payload of 60 which the translator should
# then split into 6 batches.


class DriverTest:

    def __init__(self, translator: OriginalDataScenarios,
                 test_data: DataGen):
        self.translator = translator
        self.data = test_data

    def _do_insert(self, entities: [dict]):
        try:
            tid = self.data.unique_tenant_id
            self.translator.insert_entities(tid, entities)
        finally:
            clear_insert_max_size()

    def _assert_row_count(self, expected: int):
        table = full_table_name(self.data.unique_tenant_id)
        stmt = f"select count(*) as count from {table}"
        r = self.translator.query(stmt)
        assert r[0]['count'] == expected

    def run(self, with_batches: bool):
        if with_batches:
            set_insert_max_size(self.data.insert_max_size)

        entities = self.data.generate_insert_payload()
        self._do_insert(entities)
        self._assert_row_count(len(entities))


@pytest.mark.parametrize('translator', translators,
                         ids=['timescale', 'crate'])
def test_insert_all_entities_in_one_go(translator):
    test_data = DataGen(insert_max_size=1024, min_batches=2)
    driver = DriverTest(translator, test_data)
    driver.run(with_batches=False)


@pytest.mark.parametrize('translator', translators,
                         ids=['timescale', 'crate'])
@pytest.mark.parametrize('min_batches', [2, 3, 4])
def test_insert_entities_in_batches(translator, min_batches):
    test_data = DataGen(insert_max_size=1024, min_batches=min_batches)
    driver = DriverTest(translator, test_data)
    driver.run(with_batches=True)


# NOTE. Couldn't reproduce #445.
# You can try this, but the exception I get is weirdly enough a connection
# exception. Python will crunch data in memory for about 30 mins, then the
# translator mysteriously fails w/ a connection exception, even though Crate
# is up and running...
#
# def test_huge_crate_insert(with_crate):
#     test_data = DataGen(insert_max_size=2*1024*1024, min_batches=1024)
#     #           ^ should produce at least 2GiB worth of entities!!
#     driver = TestDriver(with_crate, test_data)
#     driver.run(with_batches=True)
