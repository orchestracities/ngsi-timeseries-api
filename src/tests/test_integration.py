from src.tests.common import load_data, check_data, unload_data


def test_integration():
    load_data()
    try:
        check_data()
    finally:
        unload_data()
