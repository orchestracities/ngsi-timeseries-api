from abc import ABC, abstractmethod
from threading import Event, Thread


class BackgroundRepeater(ABC, Thread):
    """
    Run an action in a background thread at regular intervals.
    Subclasses implement the ``_do_run`` method to actually run the action
    which this thread calls every ``s`` seconds where ``s`` is a given amount
    of seconds to sleep between ``_do_run`` calls. This cycle goes on forever
    unless you call the ``kill`` method from another thread or at some point
    the ``_do_run`` returns a stop flag. Notice the ``kill`` method won't
    interrupt any ongoing invocation of ``_do_run`` (this method always runs
    to completion), so after calling the ``kill`` method, the calling thread
    should wait on this thread using the ``join`` method to ensure a clean
    exit.

    Gloriously ripped from:

    - https://stackoverflow.com/questions/323972
    """

    def __init__(self, sleep_interval: float = 1.0):
        super().__init__()
        self._kill_signal = Event()
        self._sleep_interval = sleep_interval
        self.daemon = True    # (*)
# NOTE. Daemon thread. This makes sure the program won't wait on this thread
# to complete before exiting, which is what we want b/c of the infinite loop
# in the run method. The downside is that when the Python interpreter quits,
# this thread will be interrupted abruptly. Surely this won't happen normally
# since you'd call the kill method below yourself to make this thread exit
# cleanly, wouldn't you?

    @abstractmethod
    def _do_run(self) -> bool:
        """
        Run the actual action.

        :return: ``True`` to stop the loop, ``False`` to go on.
        """
        pass

    def run(self):
        while True:
            stop = self._do_run()
            if not stop:
                # If no kill signal is set, sleep for the interval,
                # If kill signal comes in while sleeping, immediately
                #  wake up and handle
                stop = self._kill_signal.wait(self._sleep_interval)
            if stop:
                break

    def kill(self):
        """
        Interrupt the background loop and exit this thread.
        """
        self._kill_signal.set()
