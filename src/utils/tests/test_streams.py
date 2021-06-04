import pytest
from utils.streams import *


@pytest.mark.parametrize('items,how_many', [
    (None, 0), ([], 1), ([1], 2), ([1, 2], 3), ([1, 2, 3], 4),
    ([1, 2, 3, 4], 5), ([1, 2, 3, 4, 5], 10)
])
def test_ensure_min_items_fails_if_less_items_than_required(items, how_many):
    with pytest.raises(ValueError):
        ensure_min_items(how_many, items)


@pytest.mark.parametrize('initial_items,how_many', [
    ([], 0), ([1], 1), ([1, 2], 1), ([1, 2, 3], 1),
    ([1, 2, 3], 3), ([1, 2, 3, 4], 3), ([1, 2, 3, 4, 5], 3)
])
def test_ensure_min_items_returns_iter_with_same_items(
        initial_items, how_many):
    items = ensure_min_items(how_many, initial_items)
    assert initial_items == list(iter(items))
