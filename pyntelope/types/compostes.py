"""Antelope compostes data types."""


import binascii
import json
import zipfile
from pathlib import Path
from typing import Optional

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

    @pydantic.validator("type_")
    def must_be_subclass_of_antelope(cls, v):
        if not issubclass(v, AntelopeType):
            raise ValueError("Type must be subclass of AntelopeType")
        return v

    @pydantic.root_validator
    def all_values_must_be_instances_of_type(cls, all_values):
        type_ = all_values["type_"]
        values = all_values["values"]
        for value in values:
            if not isinstance(value, type_):
                msg = (
                    f"{value=} is of type={type(value)} "
                    f"but instance of {type_} was expected"
                )
                raise TypeError(msg)
        return all_values

    @classmethod
    def from_dict(cls, d: dict, /, type_: type):
        try:
            _ = iter(d)
        except TypeError:
            raise TypeError("Only iterables are supported.")

        if issubclass(type_, Primitive):
            constructor = type_
        elif issubclass(type_, Composte):
            constructor = type_.from_dict
        values = tuple(constructor(i) for i in d)
        obj = cls(values=values, type_=type_)
        return obj

    def to_dict(self):
        if issubclass(self.type_, Primitive):
            d = [i.value for i in self.values]
        elif issubclass(self.type_, Composte):
            d = [i.to_dict() for i in self.values]
        return d

    @classmethod
    def from_bytes(cls, bytes_: bytes, /, type_: type):
        length = primitives.Varuint32.from_bytes(bytes_)
        bytes_ = bytes_[len(length) :]  # NOQA: E203
        values = []
        for n in range(length.value):
            value = type_.from_bytes(bytes_)
            values.append(value)
            bytes_ = bytes_[len(value) :]  # NOQA: E203
        values = tuple(values)
        obj = cls(values=values, type_=type_)
        return obj

    def __bytes__(self):
        bytes_ = b""
        length = primitives.Varuint32(len(self.values))
        bytes_ += bytes(length)
        for value in self.values:
            bytes_ += bytes(value)
        return bytes_

    def __getitem__(self, index, /):
        sliced_values = self.values[index]
        sliced_obj = self.__class__(values=sliced_values, type_=self.type_)
        return sliced_obj


class Abi(Composte):
    comment: primitives.String
    version: primitives.String
    types: Array
    structs: Array
    actions: Array
    tables: Array
    ricardian_clauses: Array
    error_messages: Array
    abi_extensions: Array
    variants: Optional[Array]
    action_results: Optional[Array]
    kv_tables: Optional[Array]

    @classmethod
    def from_dict(cls, /, d: dict):
        comment = primitives.String(d.get("____comment", ""))
        version = primitives.String(d["version"])
        types = Array.from_dict(d.get("types", ()), type_=_AbiType)
        structs = Array.from_dict(d.get("structs", ()), type_=_AbiStruct)
        actions = Array.from_dict(d.get("actions", ()), type_=_AbiAction)
        tables = Array.from_dict(d.get("tables", ()), type_=_AbiTable)
        ricardian_clauses = Array.from_dict((), type_=primitives.String)
        error_messages = Array.from_dict(
            d.get("error_messages", ()), type_=primitives.String
        )
        abi_extensions = Array.from_dict(
            d.get("abi_extensions", ()), type_=primitives.String
        )
        variants = (
            Array.from_dict(d["variants"], type_=primitives.String)
            if "variants" in d
            else None
        )
        action_results = (
            Array.from_dict(d["action_results"], type_=primitives.String)
            if "action_results" in d
            else None
        )
        kv_tables = (
            Array.from_dict(d["kv_tables"], type_=primitives.String)
            if "kv_tables" in d
            else None
        )
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
            self.version,
            self.types,
            self.structs,
            self.actions,
            self.tables,
            self.ricardian_clauses,
            self.error_messages,
            self.abi_extensions,
        ]
        if self.variants is not None:
            attrs.append(self.variants)
        if self.action_results is not None:
            attrs.append(self.action_results)
        if self.kv_tables is not None:
            attrs.append(self.kv_tables)

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


class _AbiType(Composte):
    new_type_name: primitives.String
    json_type: primitives.String

    @classmethod
    def from_dict(cls, d: dict, /):
        new_type_name = primitives.String(d["new_type_name"])
        json_type = primitives.String(d["type"])
        o = cls(new_type_name=new_type_name, json_type=json_type)
        return o

    def to_dict(self):
        d = {
            "new_type_name": self.new_type_name.value,
            "type": self.json_type.value,
        }
        return d

    @classmethod
    def from_bytes(cls, bytes_):
        new_type_name = primitives.String.from_bytes(bytes_)
        bytes_ = bytes_[len(new_type_name) :]  # NOQA: E203
        json_type = primitives.String.from_bytes(bytes_)
        obj = cls(new_type_name=new_type_name, json_type=json_type)
        return obj

    def __bytes__(self):
        return bytes(self.new_type_name) + bytes(self.json_type)


class _AbiStructsField(Composte):
    name: primitives.String
    type_: primitives.String

    @classmethod
    def from_dict(cls, /, d: dict):
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


class _AbiStruct(Composte):
    name: primitives.String
    base: primitives.String
    fields: Array  # an array of _AbiStructsField

    @classmethod
    def from_dict(cls, /, d: dict):
        name = primitives.String(d["name"])
        base = primitives.String(d["base"])
        fields = Array.from_dict(d["fields"], type_=_AbiStructsField)
        o = cls(name=name, base=base, fields=fields)
        return o

    @classmethod
    def from_bytes(cls, bytes_):
        ...

    def __bytes__(self):
        return bytes(self.name) + bytes(self.base) + bytes(self.fields)


class _AbiAction(Composte):
    name: primitives.Name
    type_: primitives.String
    ricardian_contract: primitives.String

    @classmethod
    def from_dict(cls, /, d: dict):
        name = primitives.Name(d["name"])
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
    def from_dict(cls, /, d: dict):
        name = primitives.Name(d["name"])
        index_type = primitives.String(d["index_type"])
        key_names = Array.from_dict([], type_=primitives.String)
        key_types = Array.from_dict([], type_=primitives.String)
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

    uint8_array = Array.from_dict(uint8_values, type_=primitives.Uint8)
    return uint8_array


def _uint8_list_to_hex(uint8_list: list) -> str:
    hexcode = ""
    for int8 in uint8_list:
        hexcode += ("00" + str(format(int8.value, "x")))[-2:]
    return hexcode


def _hex_to_bin(hexcode: str) -> bytes:
    return binascii.unhexlify(hexcode.encode("utf-8"))
