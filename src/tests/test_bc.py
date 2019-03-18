from src.tests.common import check_data, unload_data


def test_backwards_compatibility():
    # NOTE: load_data() must be called using previous QL version!
    # see run_tests.sh
    try:
        check_data()
    finally:
        unload_data()
