import pytest
from typing import Optional

from utils.itersplit import IterCostSplitter


def new_splitter(batch_max_cost: int) -> IterCostSplitter:
    def cost(x: Optional[int]) -> int:
        return 0 if x is None else x

    return IterCostSplitter(cost_fn=cost, batch_max_cost=batch_max_cost)


def test_error_on_none():
    target = new_splitter(batch_max_cost=1)
    with pytest.raises(TypeError):
        target.list_batches(None)


@pytest.mark.parametrize('mx', [-1, 0, 1, 2, 3])
@pytest.mark.parametrize('empty', [[], iter([])])
def test_empty_yields_empty(mx, empty):
    target = new_splitter(batch_max_cost=mx)

    actual = target.list_batches(empty)
    assert len(actual) == 0

    xs = target.iter_batches(empty)
    actual = [x for x in xs]
    assert len(actual) == 0


@pytest.mark.parametrize('mx', [-1, 0, 1])
def test_too_small_cost_yields_singletons(mx):
    target = new_splitter(batch_max_cost=mx)

    actual = target.list_batches([2, 3, 4])
    assert actual == [[2], [3], [4]]


@pytest.mark.parametrize('in_stream',
                         [[None, 1, None, 2], iter([None, 1, None, 2])])
def test_keep_any_input_none(in_stream):
    target = new_splitter(batch_max_cost=2)

    actual = target.list_batches(in_stream)
    assert actual == [[None, 1, None], [2]]


def test_produce_all_batches_even_when_skipping_iterators():
    target = new_splitter(batch_max_cost=1)
    xs = target.iter_batches([1, 2, 3])  # ~~> [[1], [2], [3]]

    actual = []
    for k in range(3):
        next(xs)            # throwing away an iterator ...
        x = list(next(xs))  # should affect overall iteration
        actual.append(x)

    assert actual == [[1], [2], [3]]


def test_can_iter_multiple_times():
    target = new_splitter(batch_max_cost=5)
    xs = [2, 3, 4]
    expected = [[2, 3], [4]]

    actual = []
    for k in target.iter_batches(iter(xs)):
        ks = list(k)
        actual.append(ks)
    assert actual == expected

    actual = target.list_batches(xs)
    assert actual == expected


def test_typical_example():
    target = new_splitter(batch_max_cost=5)
    xs = [1, 7, 2, 3, 8, 5, 1, 2, 1]
    actual = target.list_batches(xs)
    assert actual == [[1], [7], [2, 3], [8], [5], [1, 2, 1]]
