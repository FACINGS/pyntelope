"""Abstract antelope types."""

from abc import ABC, abstractmethod

import pydantic


class AntelopeType(pydantic.BaseModel, ABC):
    @abstractmethod
    def __bytes__(self):
        """Convert instance to bytes."""

    @abstractmethod
    def from_bytes(self):
        """Create instance from bytes."""

    def __len__(self):
        """Lenght of value in bytes."""
        bytes_ = bytes(self)
        return len(bytes_)

    class Config:
        extra = "forbid"
        frozen = True


class Primitive(AntelopeType, ABC):
    def __init__(self, *args, **kwargs):
        if len(kwargs) == 1 and "value" in kwargs:
            super().__init__(value=kwargs["value"])
        else:
            super().__init__(value=args[0])


class Composte(AntelopeType, ABC):
    @abstractmethod
    def from_dict(self):
        """Instantiate class from a dict or list object."""
