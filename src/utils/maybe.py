"""
This module provides utilities to work with Python optional types.
"""

from typing import Any, Callable, Optional


def maybe_map(f: Callable[[Any], Any], value: Optional[Any]) -> Optional[Any]:
    """
    Return `f(value)` if `value` is not `None` else `None`.
    """
    if value is not None:
        return f(value)
    return None
