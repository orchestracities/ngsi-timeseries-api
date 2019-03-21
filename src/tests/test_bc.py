from src.tests.common import check_data, unload_data, create_entities


def test_backwards_compatibility():
    # NOTE: load_data() must be called using previous QL version!
    # see run_tests.sh
    entities = create_entities()
    try:
        check_data(entities)
    finally:
        unload_data(entities)
