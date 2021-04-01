import logging
from objsize import get_deep_size
from typing import Optional, Tuple

from utils.cfgreader import BitSizeVar, EnvReader
from utils.itersplit import IterCostSplitter

INSERT_MAX_SIZE_VAR = 'INSERT_MAX_SIZE'
"""
The name of the environment variable to configure the insert max size.
"""


def _log():
    return logging.getLogger(__name__)


def configured_insert_max_size_in_bytes() -> Optional[int]:
    """
    Read the insert max size env var and return its value in bytes if
    set to a parsable value or ``None`` otherwise. Notice if a value
    is present but is garbage we still return ``None`` but we also
    log a warning.

    :return: the max size in bytes if available, ``None`` otherwise.
    """
    env_reader = EnvReader(log=_log().debug)
    parsed = env_reader.safe_read(BitSizeVar(INSERT_MAX_SIZE_VAR, None))
    if parsed:
        return int(parsed.to_Byte())
    return None


def compute_row_size(r: Tuple) -> int:
    """
    Compute the memory size, in bytes, of the given row's components.

    :param r: the row to insert.
    :return: the size in bytes.
    """
    component_sizes = [get_deep_size(k) for k in r]
    return sum(component_sizes)


def to_insert_batches(rows: [Tuple]) -> [[Tuple]]:
    """
    Split the SQL rows to insert into batches so the Translator can insert
    each batch separately, i.e. issue a SQL insert statement for each batch
    as opposed to a single insert for the whole input lot. We do this since
    some backends (e.g. Crate) have a cap on how much data you can shovel
    in a single SQL (bulk) insert statement---see #445 about it.

    Split only if the insert max size env var holds a valid value. (If that's
    not the case, return a single batch with all input rows.)
    Splitting happens as explained in the ``IterCostSplitter`` docs with
    ``compute_row_size`` as a cost function so the cost of each input row
    is the amount of bytes its components take up in memory and the value
    of the env var as a maximum batch size (= cost in bytes).

    :param rows: the rows the SQL translator lined up for an insert.
    :return: the insert batches.
    """
    config_max_cost = configured_insert_max_size_in_bytes()
    if config_max_cost is None:
        return [rows]
    splitter = IterCostSplitter(cost_fn=compute_row_size,
                                batch_max_cost=config_max_cost)
    return splitter.list_batches(rows)
