from utils.maybe import *


def test_maybe_map_do_nothing_to_none():
    assert maybe_map(str, None) is None


def test_maybe_map_transform_value():
    assert maybe_map(lambda x: x + 1, 1) == 2
