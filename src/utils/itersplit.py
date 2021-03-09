"""
This module provides utilities to spilt iterables into batches.
"""

from itertools import chain
from typing import Any, Callable, Iterable


CostFn = Callable[[Any], int]
"""
A function to assign a "cost" to an item. Typically the cost is a non
negative integer.
"""


class IterCostSplitter:
    """
    Split a stream in batches so the cumulative cost of each batch is
    within a set cost goal.
    Given an input stream ``s`` and a cost function ``c``, produce a
    sequence of streams ``b`` such that joining the ``b`` streams
    yields ``s`` and, for each ``b`` stream of length ``> 1``, mapping
    ``c`` to each element and summing the costs yields a value ``≤ M`,
    where ``M`` is a set cost goal. In symbols:

        1. s = b[0] + b[1] + ...
        2. b[k] = [x1, x2, ...] ⟹ M ≥ c(x1) + c(x2) + ...

    Notice it can happen that to make batches satisfying (1) and (2),
    some ``b[k]`` contains just one element ``x > M`` since that doesn't
    violate (1) and (2).

    Examples:

    >>> splitter = IterCostSplitter(cost_fn=lambda x: x, batch_max_cost=5)
    >>> splitter.list_batches([1, 7, 2, 3, 8, 5, 1, 2, 1])
    [[1], [7], [2, 3], [8], [5], [1, 2, 1]]
    """

# NOTE. Algebra of programming.
# For the mathematically inclined soul out there, the Python implementation
# below is based on this maths spec of sorts, using FP-like syntax for lists
#
#    ϕ []          = []
#    ϕ [x]         = [[x]]
#    ϕ [x, y, ...] = [ x:t, u, ...]       if c(x) + Σ c(t[i]) ≤ M
#    ϕ [x, y, ...] = [ [x], t, u, ...]    otherwise
#
# where  [t, u, ...] = ϕ [y, ...]
# Or if you can read Haskell:
#
#     ϕ :: [Int] -> [[Int]]
#     ϕ []                = []
#     ϕ [x]               = [[x]]
#     ϕ (x:xs)
#       | c x + s y ≤ m   = (x:y) : ys
#       | otherwise       = [x]   : y : ys
#       where
#         (y:ys) = ϕ xs
#         c = ...your cost function
#         m = ...your cost goal
#         s = sum . map c
#
# Why is the Python implementation so damn complicated then?! The mind
# boggles.

    def __init__(self, cost_fn: CostFn, batch_max_cost: int):
        """
        Create a new instance.

        :param cost_fn: the function to assign a cost to each stream element.
        :param batch_max_cost: the cost goal. It determines how the input
            stream gets split into batches.
        """
        self._cost_of = cost_fn
        self._max_cost = batch_max_cost
        self._iter = None
        self._keep_iterating = True

    def _put_back(self, item: Any):
        self._iter = chain([item], self._iter)

    def _is_empty(self) -> bool:
        try:
            x = next(self._iter)
            self._put_back(x)
            return False
        except StopIteration:
            return True

    def _next_batch(self) -> Iterable[Any]:
        cost_so_far = 0
        batch_size = 0

        for x in self._iter:
            next_cost = self._cost_of(x)

            if batch_size == 0 or cost_so_far + next_cost <= self._max_cost:
                batch_size += 1
                cost_so_far += next_cost
                yield x
            else:
                self._put_back(x)
                return

        self._keep_iterating = False

    def iter_batches(self, xs: Iterable[Any]) -> Iterable[Iterable[Any]]:
        """
        Split ``xs`` in batches so the cumulative cost of each batch is
        no greater than the ``batch_max_cost`` given to this class'
        constructor.

        :param xs: the stream to split.
        :return: a stream of streams (batches) with the two properties
            documented in this class' description.
        """
        self._iter = iter(xs)
        if self._is_empty():
            return self._iter

        self._keep_iterating = True
        while self._keep_iterating:
            yield self._next_batch()

    def list_batches(self, xs: Iterable[Any]) -> [[Any]]:
        """
        Same as ``iter_batches`` but force the streams into a list, i.e.
        consume all iterators to produce a list of lists.
        """
        return [list(ys) for ys in self.iter_batches(xs)]
