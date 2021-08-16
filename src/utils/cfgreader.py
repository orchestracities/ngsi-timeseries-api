"""
This module provides utilities to read configuration values from environment
variables, YAML files, etc.
"""

import bitmath
from bitmath import Bitmath
import logging
import os
from typing import Union
import yaml


MaybeString = Union[str, None]


class EVar:
    """
    Defines an interface for environment variable parsers.
    """

    @staticmethod
    def has_value(str_rep: MaybeString) -> bool:
        """
        Does the input string have at least one non-whitespace char?

        :param str_rep: the variable value as read from the environment.
        :return: true if yes, false otherwise.
        """
        return str_rep is not None and len(str_rep.strip()) > 0

    def __init__(self, var_name: str, default_value, mask_value=False):
        self.name = var_name
        self.default_value = default_value
        self.mask_value = mask_value

    def read(self, rep: MaybeString):
        """
        Parse the value from its string representation as read from the
        environment.

        :param rep: the env value.
        :return: the parsed value if the string rep holds a value,
            the default value otherwise.
        """
        if self.has_value(rep):
            return self._do_read(rep)
        return self.default_value

    def _do_read(self, rep: str):
        pass


class StrVar(EVar):
    """
    An env value parsed as a string. The string representation gets stripped
    of any leading and trailing whitespace.
    """

    def _do_read(self, rep: str) -> str:
        return rep.strip()


class IntVar(EVar):
    """
    An env value parsed as an integer.
    """

    def _do_read(self, rep: str) -> int:
        return int(rep)


class FloatVar(EVar):
    """
    An env value parsed as an integer.
    """

    def _do_read(self, rep: str) -> float:
        return float(rep)


class BoolVar(EVar):
    """
    An env value parsed as a boolean. It evaluates to true just in case the
    string representation, after trimming any leading and trailing whitespace,
    is equal, ignoring case, to any of: 'true', 'yes', '1', 't'.
    """

    def _do_read(self, rep: str) -> bool:
        return rep.strip().lower() in ('true', 'yes', '1', 't', 'y')


class BitSizeVar(EVar):
    """
    An env value parsed as a digital information size, e.g. file size in
    giga bytes, memory size in mega bytes, word size in bits, etc. This
    class is just a wrapper around the ``bitmath`` lib, see there for
    usage and examples.
    """

    def _do_read(self, rep: str) -> Bitmath:
        return bitmath.parse_string(rep)


class EnvReader:
    """
    Reads environment variables.
    """

    @staticmethod
    def get_log_msg(var: EVar, value: MaybeString) -> str:
        msgs = {
            # (has value, mask value)
            (True, True): "Env variable {name} set, using its value.",
            (True, False): "Env variable {name} set to '{value}', " + \
                           "using this value.",
            (False, True): "Env variable {name} not set, " + \
                           "using default value.",
            (False, False): "Env variable {name} not set, " + \
                            "using default value of: {default_value}"
        }
        return msgs[var.has_value(value), var.mask_value].format(
            name=var.name, value=value, default_value=var.default_value
        )

    @staticmethod
    def get_parse_error_log_msg(var: EVar, cause: Exception) -> str:
        return f"Error reading env variable {var.name}: {cause}; " + \
            f"using default value of {var.default_value}."

    def __init__(self, var_store: dict = os.environ, log=None):
        self.var_store = var_store
        self.log = log if log else logging.getLogger(__name__).debug

    def read(self, var: EVar):
        """
        Read the specified environment variable and, if set, parse its
        value; otherwise return the variable default.
        Also log the value as read if it's not supposed to be masked.

        :param var: the variable to read.
        :return: the parsed value if the variable is set, the variable's
            default otherwise.
        """
        env_value = self.var_store.get(var.name)
        msg = self.get_log_msg(var, env_value)
        self.log(msg)
        return var.read(env_value)

    def safe_read(self, var: EVar):
        """
        Same as `read` but return variable's default value if the one
        found in the environment can't be parsed and log the error.
        """
        try:
            return self.read(var)
        except ValueError as e:
            msg = self.get_parse_error_log_msg(var, e)
            self.log(msg)
            return var.default_value


class YamlReader:
    """
    Reads YAML files.
    """

    @staticmethod
    def get_log_msg(path):
        if EVar.has_value(path):
            return f"using config file: {path}"
        return f"no config file specified, using defaults."

    def __init__(self, var_store: dict = os.environ, log=None):
        self.var_store = var_store
        self.log = log if log else logging.getLogger(__name__).debug

    def from_file(self, path: MaybeString, defaults: dict) -> dict:
        """
        Read the YAML in the specified file.

        :param path: the path to the file.
        :param defaults: what to return if the path is empty.
        :return: the YAML file as a dictionary if the path isn't empty,
            the default dictionary otherwise.
        """
        msg = self.get_log_msg(path)
        self.log(msg)

        if EVar.has_value(path):
            file = open(path)
            return yaml.safe_load(file)
        return defaults

    def from_env_file(self, env_var_name: str, defaults: dict) -> dict:
        """
        Read the YAML in the file pointed to by the given env variable.

        :param env_var_name: the env variable name. It's value is supposed
            to be a file path.
        :param defaults: what to return if the path is empty.
        :return: the YAML file as a dictionary if the path isn't empty,
            the default dictionary otherwise.
        """
        reader = EnvReader(var_store=self.var_store, log=self.log)
        path = reader.read(StrVar(env_var_name, ''))
        return self.from_file(path, defaults)
