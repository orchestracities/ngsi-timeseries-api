from itertools import islice, chain
from typing import Iterable, Any


def ensure_min_items(how_many: int, items: Iterable[Any]) -> Iterable[Any]:
    """
    Ensure the given iterable contains the specified minimum amount of items.
    After calling this method you'll have to discard the input iterator and
    use the one returned by this method in its place.
    :param how_many: minimum number of items required in the iterator.
    :param items: the iterator to check.
    :return: a new iterator identical to the input one.
    :raise ValueError: if the iterator is ``None`` or doesn't have the required
        minimum number of items in it.
    """
    if items is not None:
        it = iter(items)
        init = list(islice(it, None, how_many))
        if how_many == len(init):
            return chain(init, it)
    raise ValueError
