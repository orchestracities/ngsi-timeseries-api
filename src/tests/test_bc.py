from tests.common import check_data, unload_data, create_entities, \
    check_deleted_data


def test_backwards_compatibility():
    # NOTE: load_data() must be called using previous QL version!
    # see run_tests.sh
    entities = create_entities()
    assert len(entities) > 1
    try:
        check_data(entities)
    finally:
        unload_data(entities)
        check_deleted_data(entities)
