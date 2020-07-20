from translators.sql_translator import METADATA_TABLE_NAME, TYPE_PREFIX
from conftest import crate_translator as translator
from utils.common import create_random_entities


def test_default_replication(translator):
    """
    By default there should be 2-all replicas

    https://crate.io/docs/crate/reference/en/latest/general/ddl/replication.html
    """
    entities = create_random_entities(1, 2, 10)
    entity = entities[0]
    e_type = entity['type']

    translator.insert(entities)

    et = '{}{}'.format(TYPE_PREFIX, e_type.lower())
    # same as in translator._et2tn but without double quotes
    op = "select number_of_replicas from information_schema.tables where " \
         "table_name = '{}'"
    translator.cursor.execute(op.format(et))
    res = translator.cursor.fetchall()
    assert res[0] == ['2-all']

    # Metadata table should also be replicated
    translator.cursor.execute(op.format(METADATA_TABLE_NAME))
    res = translator.cursor.fetchall()
    assert res[0] == ['2-all']
