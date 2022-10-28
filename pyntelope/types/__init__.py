import sys

from .base import AntelopeType, Composte, Primitive
from .compostes import *  # NOQA: F403
from .primitives import *  # NOQA: F403


def _get_all_types():
    def is_eostype(class_):
        if isinstance(class_, type):
            if issubclass(class_, AntelopeType) and class_ is not AntelopeType:
                return True
        return False

    classes = list(sys.modules[__name__].__dict__.items())

    all_types = {
        name.lower(): class_ for name, class_ in classes if is_eostype(class_)
    }
    return all_types


_all_types = _get_all_types()


def from_string(type_: str) -> AntelopeType:
    """Return an AntelopeType object from a given string."""
    type_ = type_.lower()
    try:
        class_ = _all_types[type_]
    except KeyError:
        types = list(_all_types.keys())
        msg = f"Type {type_} not found. List of available {types=}"
        raise ValueError(msg)
    return class_
