import os
from src.tests.common import load_data, check_data, unload_data, \
    check_deleted_data


def test_cors_allowed_headers():
    entities = []
    try:
        entities = load_data()
        assert len(entities) > 1

    finally:
        unload_data(entities)