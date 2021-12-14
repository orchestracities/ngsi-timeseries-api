from abc import ABC, abstractmethod
import struct

import pg8000
import crate.client.exceptions


class ErrorAnalyzer(ABC):
    """
    Tells what kind of errors a translator got.
    One subclass in correspondence of each translator.
    Every instance gets created with an error occurred while using the
    corresponding translator.
    """

    @abstractmethod
    def error(self) -> Exception:
        """
        :return: the error this instance is for.
        """
        pass

    @abstractmethod
    def is_transient_error(self) -> bool:
        """
        Is the error transient? e.g. a connection failure.

        :return: ``True`` for yes, ``False`` for no.
        """
        pass

    @abstractmethod
    def is_aggregation_error(self) -> bool:
        """
        Is aggregation error? e.g. Aggregation method sum
        cannot be applied on bool.

        :return: ``True`` for yes, ``False`` for no.
        """
        pass

    def can_retry_insert(self) -> bool:
        """
        Take an error raised by the ``insert`` method and decide if you
        can retry the insert. Typically the answer is yes if the input
        is a transient error, e.g. a connection failure. This method has
        a default implementation that calls ``is_transient_error``,
        subclasses should override it if needed.

        :return: ``True`` for yes, you can retry the insert; ``False``
            for no.
        """
        return self.is_transient_error()


class PostgresErrorAnalyzer(ErrorAnalyzer):

    def __init__(self, error: Exception):
        self._error = error

    def error(self) -> Exception:
        return self._error

    def is_aggregation_error(self) -> bool:
        e = self._error
        if isinstance(e, pg8000.ProgrammingError):
            return len(e.args) > 0 and isinstance(e.args[0], dict) \
                and e.args[0].get('C', '') == '42883'

    def is_transient_error(self) -> bool:
        e = self._error
        if isinstance(e, struct.error):                    # (1)
            msg = str(e)
            return msg.startswith('unpack_from requires a buffer')

        if isinstance(e, pg8000.ProgrammingError):         # (5)
            return len(e.args) > 0 and isinstance(e.args[0], dict) \
                and e.args[0].get('C', '') == '55000'

        return isinstance(e, ConnectionError) or \
            isinstance(e, pg8000.InterfaceError)           # (2), (3), (4)
# NOTE. Transient errors.
# 1. Socket reads. If the connection goes down while pg8000 is reading from
# the socket, there will be less bytes in the underlying C socket than pg8000
# expects and a struct.error gets raised with a message similar to:
# "unpack_from requires a buffer of at least 5 bytes for unpacking 5 bytes at
# offset 0 (actual buffer size is 0)"
# 2. Socket writes. If the connection goes down while pg8000 is writing to
# the socket, a ConnectionError gets raised, e.g.
#   BrokenPipeError: [Errno 32] Broken pipe
# (BrokenPipeError is a subclass of ConnectionError)
# 3. Connections errors. Supposedly get thrown as ConnectionError exceptions?
# 4. DB transient errors. These are errors in the DB, not a programming error
# on the QL side. They get thrown as InterfaceError exceptions.
# 5. Connection errors masquerading as programming errors. I've bumped into a
# weird error where the DB couldn't accept connections but pg8000 thinks it's
# a programming error (how is the client supposed to know, you may wonder) and
# so it wraps e.g. this Postgres error:
# - https://github.com/postgres/postgres/blob/REL_12_0/src/backend/utils/init/postinit.c#L354
# with a pg8000.ProgrammingError. (ERRCODE_OBJECT_NOT_IN_PREREQUISITE_STATE
# is 55000.)


class CrateErrorAnalyzer(ErrorAnalyzer):

    def __init__(self, error: Exception):
        self._error = error

    def error(self) -> Exception:
        return self._error

    def is_aggregation_error(self) -> bool:
        e = self._error
        if isinstance(e, crate.client.exceptions.ProgrammingError):
            return 'Cannot cast' in e.message or 'UnsupportedFeatureException' in e.message

    def is_transient_error(self) -> bool:
        return isinstance(self._error,
                          crate.client.exceptions.ConnectionError)
