"""
Flushing of time series memory buffers to permanent storage.
Each buffer is saved to its own file to avoid race conditions among processes
and threads. Saving of data is efficient since it's based on streams and
lock-free, i.e. there's no need to acquire global locks to coordinate
writers. Files are written to a configured target directory atomically and
with unique names. This avoids interference with other programs that may be
processing previously written files. For example, another program can safely
scan the directory, aggregate data in each file, process the aggregate and
then delete the processed files with no risk of race conditions w/r/t the
writers in this module.
"""

import csv
import os
from tempfile import gettempdir
from uuid import uuid4

from server.telemetry.observation import ObservationStore, \
    ObservationStoreAction, tabulate


OBSERVATION_STORE_HEADER = ['Timepoint', 'Measurement', 'Label', 'PID']
"""
Header of the CSV file where observation store contents get written.
"""


def flush_to_csv(target_dir: str, filename_prefix: str) \
        -> ObservationStoreAction:
    """
    Build an action to stream the contents of an observation store to a CSV
    file. Write the file *atomically* to the specified target directory and
    with a unique file name. Write CSV fields in this order: time point,
    measurement, label, PID. Notice PID is the process ID of the current
    process which isn't part of the observation store but is added by this
    function to each row.

    :param target_dir: the directory where to write the file.
    :param filename_prefix: a string to prepend to the generated unique file
        name.
    :return: a function that takes an observation store and writes its contents
        to file.
    """
    return lambda store: _save_csv(target_dir, filename_prefix, store)


def _save_csv(target_dir: str, filename_prefix: str,
              store: ObservationStore):
    filename = _filename(filename_prefix)
    temp_path = os.path.join(gettempdir(), filename)
    target_path = os.path.join(target_dir, filename)

    _write_csv(temp_path, store)
    os.rename(temp_path, target_path)    # (*)

    # NOTE. Atomic move. Rename is atomic but won't work across file systems,
    # see
    # - https://alexwlchan.net/2019/03/atomic-cross-filesystem-moves-in-python/


def _filename(filename_prefix: str) -> str:
    fid = uuid4().hex
    return f"{filename_prefix}.{fid}.csv"


def _write_csv(path: str, content: ObservationStore):
    pid = os.getpid()
    ts = ((t, m, k, pid) for t, m, k in tabulate(content))    # (1)
    with open(path, mode='w') as fd:
        w = csv.writer(fd, delimiter=',', quotechar='"',
                       quoting=csv.QUOTE_MINIMAL)             # (2)
        w.writerow(OBSERVATION_STORE_HEADER)
        w.writerows(ts)

    # NOTES.
    # 1. Lazy evaluation. Parens, contrary to square brackets, don't force
    # evaluation, so we won't wind up with double the memory of the store.
    # See:
    # - https://stackoverflow.com/questions/18883414
    # 2. CSV quoting. Only quoting fields if they contain a delimiter or the
    # quote char.
