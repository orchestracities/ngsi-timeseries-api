from translators.crate import METADATA_TABLE_NAME
from translators.fixtures import crate_translator as translator
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
    translator._refresh([e_type])

    op = "select number_of_replicas from information_schema.tables where " \
         "table_name = '{}'"
    translator.cursor.execute(op.format(translator._et2tn(e_type)))
    res = translator.cursor.fetchall()
    assert res[0] == ['2-all']

    # Metadata table should also be replicated
    translator.cursor.execute(op.format(METADATA_TABLE_NAME))
    res = translator.cursor.fetchall()
    assert res[0] == ['2-all']

