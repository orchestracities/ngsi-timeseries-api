from src.tests.common import load_data, check_data, unload_data, \
    check_deleted_data


def test_integration():
    entities = []
    try:
        entities = load_data()
        assert len(entities) > 1
        check_data(entities)
    finally:
        unload_data(entities)
        check_deleted_data(entities)
