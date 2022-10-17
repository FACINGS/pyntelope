"""Antelope compostes data types."""


import binascii
import json
import zipfile
from pathlib import Path
from typing import List

import pydantic

from . import primitives
from .base import AntelopeType, Composte, Primitive


class Wasm(Primitive):
    value: bytes

    @classmethod
    def from_file(cls, file: Path, *, extension: str = ".wasm"):
        """Create a wasm object from a .wasm or from a zipped file."""
        file_contents = _load_bin_from_file(file=file, extension=extension)
        return cls(value=file_contents)

    def to_hex(self):
        return _bin_to_hex(self.value)

    def __bytes__(self):
        uint8_array = _hex_to_uint8_array(self.to_hex())
        return bytes(uint8_array)

    @classmethod
    def from_bytes(cls, bytes_):
        uint8_array = Array.from_bytes(bytes_=bytes_, type_=primitives.Uint8)
        uint8_list = uint8_array.values
        hexcode = _uint8_list_to_hex(uint8_list)
        value = _hex_to_bin(hexcode)
        return cls(value=value)


class Array(Composte):
    values: tuple
    type_: type

    @classmethod
    def from_dict(self, d: List, /):
        ...

    @pydantic.validator("type_")
    def must_be_subclass_of_antelope(cls, v):
        if not issubclass(v, AntelopeType):
            raise ValueError("Type must be subclass of AntelopeType")
        return v

    @classmethod
    def from_bytes(cls, bytes_, type_):
        length = primitives.Varuint32.from_bytes(bytes_)
        bytes_ = bytes_[len(length) :]  # NOQA: E203
        values = []
        for n in range(length.value):
            value = type_.from_bytes(bytes_)
            values.append(value.value)
            bytes_ = bytes_[len(value) :]  # NOQA: E203
        return cls(values=values, type_=type_)

    @pydantic.root_validator(pre=True)
    def all_must_satisfy_type_value(cls, all_values):
        type_ = all_values["type_"]
        values = all_values["values"]
        if len(values) >= 1:
            if issubclass(type_, Primitive):
                values = tuple(type_(v) for v in values)
            elif issubclass(type_, Composte):
                values = tuple(type_.from_dict(v) for v in values)
            else:
                msg = f"Type {type(type_)} not supported."
                raise TypeError(msg)
        else:
            values = tuple()
        all_values["values"] = values
        return all_values

    def __bytes__(self):
        bytes_ = b""
        length = primitives.Varuint32(len(self.values))
        bytes_ += bytes(length)
        for value in self.values:
            bytes_ += bytes(value)
        return bytes_

    def __getitem__(self, index):
        return Array(values=self.values[index], type_=self.type_)


class Abi(Composte):
    version: primitives.String
    types: Array
    structs: Array
    actions: Array
    tables: Array
    ricardian_clauses: Array
    error_messages: primitives.String
    abi_extensions: primitives.String
    variants: Array
    action_results: Array
    kv_tables: Array
    comment: primitives.String

    @classmethod
    def from_dict(cls, d: dict, /):
        comment = primitives.String(d.get("____comment", ""))
        version = primitives.String(d["version"])
        types = Array(type_=primitives.String, values=d["types"])
        structs = Array(type_=_AbiStructs, values=d["structs"])
        structs = Array(type_=_AbiStructs, values=[])
        actions = Array(type_=_AbiAction, values=d["actions"])
        tables = Array(type_=_AbiTable, values=d["tables"])
        kv_tables = Array(type_=primitives.String, values=[])
        ricardian_clauses = Array(type_=primitives.String, values=[])
        error_messages = primitives.String("")
        abi_extensions = primitives.String("")
        variants = Array(type_=primitives.String, values=[])
        action_results = Array(type_=primitives.String, values=[])
        o = cls(
            version=version,
            types=types,
            structs=structs,
            actions=actions,
            tables=tables,
            ricardian_clauses=ricardian_clauses,
            error_messages=error_messages,
            abi_extensions=abi_extensions,
            variants=variants,
            action_results=action_results,
            kv_tables=kv_tables,
            comment=comment,
        )
        return o

    @classmethod
    def from_file(cls, file: Path, *, extension: str = ".abi"):
        """Create a abi object from a .abi or from a zipped file."""
        file_contents_bin = _load_bin_from_file(file=file, extension=extension)
        file_contents_dict = json.loads(file_contents_bin)
        abi_obj = cls.from_dict(file_contents_dict)
        return abi_obj

    def to_hex(self):
        attrs = [
            # self.version,
            # self.types,
            # self.structs,
            self.actions,
            self.tables,
            self.ricardian_clauses,
            self.error_messages,
            self.abi_extensions,
            self.variants,
            self.action_results,
            self.kv_tables,
        ]
        b = b""
        for attr in attrs:
            b += bytes(attr)
        h = _bin_to_hex(b)
        return h

    def __bytes__(self):
        hexcode = self.to_hex()
        uint8_array = _hex_to_uint8_array(hexcode)
        return bytes(uint8_array)

    @classmethod
    def from_bytes(cls, bytes_):
        ...


class _AbiStructsField(Composte):
    name: primitives.String
    type_: primitives.String

    @classmethod
    def from_dict(cls, d: dict, /):
        name = primitives.String(d["name"])
        type_ = primitives.String(d["type"])
        return cls(name=name, type_=type_)

    @classmethod
    def from_bytes(cls, bytes_):
        name = primitives.String.from_bytes(bytes_)
        type_ = primitives.String.from_bytes(bytes_[len(name) :])  # NOQA: E203
        return cls(name=name, type_=type_)

    def __bytes__(self):
        return bytes(self.name) + bytes(self.type_)


class _AbiStructs(Composte):
    name: primitives.String
    base: primitives.String
    fields: Array  # an array of _AbiStructsField

    @classmethod
    def from_dict(cls, d: dict, /):
        name = primitives.String(d["name"])
        base = primitives.String(d["base"])
        fields = Array(values=d["fields"], type_=_AbiStructsField)
        o = cls(name=name, base=base, fields=fields)
        return o

    @classmethod
    def from_bytes(cls, bytes_):
        ...

    def __bytes__(self):
        ...


class _AbiAction(Composte):
    name: primitives.String
    type_: primitives.String
    ricardian_contract: primitives.String

    @classmethod
    def from_dict(cls, d: dict, /):
        name = primitives.String(d["name"])
        type_ = primitives.String(d["type"])
        ric_contract = primitives.String(d["ricardian_contract"])
        o = cls(name=name, type_=type_, ricardian_contract=ric_contract)
        return o

    @classmethod
    def from_bytes(self, bytes_):
        ...

    def __bytes__(self):
        b = bytes(self.name) + bytes(self.type_)
        b += bytes(self.ricardian_contract)
        return b


class _AbiTable(Composte):
    name: primitives.Name
    index_type: primitives.String
    key_names: Array
    key_types: Array
    type_: primitives.String

    @classmethod
    def from_dict(cls, d: dict, /):
        name = primitives.Name(d["name"])
        index_type = primitives.String(d["index_type"])
        key_names = Array(type_=primitives.String, values=[])
        key_types = Array(type_=primitives.String, values=[])
        type_ = primitives.String(d["type"])
        o = cls(
            name=name,
            index_type=index_type,
            key_names=key_names,
            key_types=key_types,
            type_=type_,
        )
        return o

    def __bytes__(self):
        b = bytes(self.name) + bytes(self.index_type) + bytes(self.key_names)
        b += bytes(self.key_types) + bytes(self.type_)
        return b

    @classmethod
    def from_bytes(cls, bytes_):
        ...


def _load_bin_from_file(*, file: Path, extension: str):
    if isinstance(file, Path):
        fullpath = file
    else:
        fullpath = Path().resolve() / Path(file)

    if fullpath.suffix == ".zip":
        with zipfile.ZipFile(fullpath) as zp:
            zip_path = str(fullpath.stem) + extension
            with zp.open(zip_path, mode="r") as f:
                file_contents = f.read()

    else:
        with open(fullpath, "rb") as f:
            file_contents = f.read()

    return file_contents


def _bin_to_hex(bin: bytes) -> str:
    return str(binascii.hexlify(bin).decode("utf-8"))


def _hex_to_uint8_array(hex_string: str) -> Array:
    if len(hex_string) % 2:
        msg = "Odd number of hex digits in input file."
        raise ValueError(msg)

    bin_len = int(len(hex_string) / 2)
    uint8_values = []

    for i in range(0, bin_len):
        try:
            x = int(hex_string[(i * 2) : (i * 2 + 2)], base=16)  # NOQA: E203
        except ValueError:
            msg = "Issue converting hex to uint 8 array, Invalid hex string."
            raise ValueError(msg)
        uint8_values.append(x)

    uint8_array = Array(type_=primitives.Uint8, values=uint8_values)
    return uint8_array


def _uint8_list_to_hex(uint8_list: list) -> str:
    hexcode = ""
    for int8 in uint8_list:
        hexcode += ("00" + str(format(int8.value, "x")))[-2:]
    return hexcode


def _hex_to_bin(hexcode: str) -> bytes:
    return binascii.unhexlify(hexcode.encode("utf-8"))
