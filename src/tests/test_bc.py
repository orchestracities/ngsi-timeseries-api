from tests.common import check_data, unload_data, create_entities, \
    check_deleted_data, update_data, UPDATES


def test_backwards_compatibility():
    # NOTE: load_data() must be called using previous QL version!
    # see run_tests.sh
    entities = create_entities(old=False)
    assert len(entities) > 1
    try:
        check_data(entities)
        #add more data
        update_data(entities, updates=1)
        check_data(entities, check_n_indexes=True, updates=UPDATES + 1)
    finally:
        unload_data(entities)
        check_deleted_data(entities)
