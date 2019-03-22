from src.tests.common import load_data, check_data, unload_data


def test_integration():
    entities = []
    try:
        entities = load_data()
        check_data(entities)
    finally:
        unload_data(entities)
