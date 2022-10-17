"""Antelope "primitive" data types."""

import binascii
import calendar
import datetime as dt
import json
import re
import struct
import sys
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

import pydantic


class AntelopeType(pydantic.BaseModel, ABC):
    @pydantic.validator("value", pre=True, check_fields=False)
    def check_if_same_type(cls, v):
        if type(v) is cls:
            return v.value
        return v

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


class UnixTimestamp(Primitive):
    """
    Serialize a datetime.

    Precision is in seconds
    Considers UTC time
    """

    value: dt.datetime

    @pydantic.validator("value")
    def remove_everything_bellow_seconds(cls, v):
        new_v = v.replace(microsecond=0)
        return new_v

    def __bytes__(self):
        unix_secs = calendar.timegm(self.value.timetuple())
        uint32_secs = Uint32(value=unix_secs)
        bytes_ = bytes(uint32_secs)
        return bytes_

    @classmethod
    def from_bytes(cls, bytes_):
        uint32_secs = Uint32.from_bytes(bytes_)
        datetime = dt.datetime.utcfromtimestamp(uint32_secs.value)
        return cls(value=datetime)


class Bool(Primitive):
    value: bool

    def __bytes__(self):
        return b"\x01" if self.value else b"\x00"

    @classmethod
    def from_bytes(cls, bytes_):
        return cls(value=int(bytes_[:1].hex(), 16))


class String(Primitive):
    value: str

    def __bytes__(self):
        bytes_ = self.value.encode("utf8")
        length = len(bytes_)
        bytes_ = bytes(Varuint32(value=length)) + bytes_
        return bytes_

    @pydantic.validator("value")
    def must_not_contain_multi_utf_char(cls, v):
        if len(v) < len(v.encode("utf8")):
            msg = (
                f'Input "{v}" has a multi-byte utf character in it, '
                "currently pyntelope does not support serialization of "
                "multi-byte utf characters."
            )
            raise ValueError(msg)
        return v

    @classmethod
    def from_bytes(cls, bytes_):
        size = Varuint32.from_bytes(bytes_)
        start = len(size)
        string_bytes = bytes_[start : start + size.value]  # NOQA: E203
        value = string_bytes.decode("utf8")
        return cls(value=value)


class Asset(Primitive):
    """
    Serialize a Asset.

    serializes an amount (can be a float value) and currency name together
    uses Symbol type to serialize percision and name of currency,
    uses Uint64 type to serialize amount
    amount and name are seperated by one space
    example: 50.100000 WAX
    """

    value: str

    def get_name(self):
        """
        Extract the name from a raw Asset string.

        example: "WAX" from Asset string "99.1000000 WAX"
        """
        stripped_value = self.value.strip()
        return stripped_value.split(" ")[1]

    def get_int_digits(self):
        """
        Extract the integer digits (digits before the decimal).

        from raw Asset string
        example: "99" from Asset string "99.1000000 WAX"
        """
        stripped_value = self.value.strip()
        pos = 0
        int_digits = ""

        # check for negative sign
        if stripped_value[pos] == "-":
            int_digits += "-"
            pos += 1

        curr_char = stripped_value[pos]

        # get amount value
        while (
            pos < len(stripped_value) and curr_char >= "0" and curr_char <= "9"
        ):
            int_digits += curr_char
            pos += 1
            curr_char = stripped_value[pos]

        return int_digits

    def get_frac_digits(self):
        """
        Extract the decimal digits as integers (digits after the decimal).

        example: "1000000" from Asset string "99.1000000 WAX"
        """
        stripped_value = self.value.strip()
        pos = 0
        precision = 0
        frac_digits = ""
        curr_char = 0

        if "." in stripped_value:
            pos = stripped_value.index(".") + 1
            curr_char = stripped_value[pos]
            while (
                pos < len(stripped_value)
                and curr_char >= "0"  # noqa: W503
                and curr_char <= "9"  # noqa: W503
            ):
                frac_digits += curr_char
                pos += 1
                curr_char = stripped_value[pos]
                precision += 1

        else:
            return ""

        return frac_digits

    def get_precision(self):
        """
        Get the precision (number of digits after decimal).

        example: "7" from Asset string "99.1000000 WAX"
        """
        return len(self.get_frac_digits())

    def __bytes__(self):

        amount = Uint64(int(self.get_int_digits() + self.get_frac_digits()))
        name = self.get_name()
        symbol = Symbol(str(self.get_precision()) + "," + name)

        amount_bytes = bytes(amount)
        symbol_bytes = bytes(symbol)

        return amount_bytes + symbol_bytes

    @classmethod
    def from_bytes(cls, bytes_):
        amount_bytes = bytes_[:8]  # get first 8 bytes
        asset_precision = bytes_[8]  # (amount of decimal places)
        amount = str(
            struct.unpack("<Q", amount_bytes)[0]
        )  # amount with decimal values (no decimal splitting yet)
        # get name (currency) from Symbol
        name = str(Symbol.from_bytes(bytes_[8:])).split(",")[1][:-1]
        if asset_precision == 0:
            value = amount + " " + name
        else:
            value = (
                amount[:-asset_precision]
                + "."  # noqa: W503
                + amount[asset_precision + 1 :]  # noqa: W503, E203
                + " "  # noqa: W503
                + name  # noqa: W503
            )  # combine everything and place decimal in correct position
        return cls(value=value)

    @pydantic.validator("value")
    def amount_must_be_in_the_valid_range(cls, v):
        value_list = str(v).strip().split(" ")
        if len(value_list) != 2:
            msg = (
                f'Input "{v}" must have exactly one space in between '
                "amount and name"
            )
            raise ValueError(msg)
        return v

    @pydantic.validator("value")
    def check_for_frac_digit_if_decimal_exists(cls, v):
        stripped_value = v.strip()
        if "." in stripped_value:
            pos = stripped_value.index(".") + 1
            curr_char = stripped_value[pos]
            if (
                pos < len(stripped_value)
                and curr_char >= "0"  # noqa: W503
                and curr_char <= "9"  # noqa: W503
            ):
                return v
            else:
                msg = (
                    "decimal provided but no fractional digits were provided."
                )
                raise ValueError(msg)
        return v

    @pydantic.validator("value", allow_reuse=True)
    def check_if_amount_is_valid(cls, v):
        stripped_value = v.strip()
        amount = float(stripped_value.split(" ")[0])
        if amount < 0 or amount > 18446744073709551615:
            msg = f'amount "{amount}" must be between 0 and ' "2^64 inclusive."
            raise ValueError(msg)
        return v

    @pydantic.validator("value", allow_reuse=True)
    def check_if_name_is_valid(cls, v):
        stripped_value = v.strip()
        name = stripped_value.split(" ")[1]
        match = re.search("^[A-Z]{1,7}$", name)
        if not match:
            msg = f'Input "{name}" must be A-Z and between 1 to 7 characters.'
            raise ValueError(msg)
        return v


class Symbol(Primitive):
    """
    Serialize a Symbol.

    serializes a percision and currency name together
    precision is used to indicate how many decimals there
    are in an Asset type amount
    precision and name are seperated by a commma
    example: 1,WAX
    """

    value: str

    @pydantic.validator("value", allow_reuse=True)
    def name_must_be_of_valid_length(cls, v):
        name = v.split(",")[1]
        match = re.search("^[A-Z]{1,7}$", name)
        if not match:
            msg = f'Input "{name}" must be A-Z and between 1 to 7 characters.'
            raise ValueError(msg)
        return v

    @pydantic.validator("value", allow_reuse=True)
    def precision_must_be_in_the_valid_range(cls, v):
        precision = int(v.split(",")[0])
        if precision < 0 or precision > 16:
            msg = (
                f'precision "{precision}" must be between 0 and '
                "16 inclusive."
            )
            raise ValueError(msg)
        return v

    def __bytes__(self):
        precision = int(self.value.split(",")[0])
        precision_bytes_ = struct.pack("<B", (precision & 0xFF))
        bytes_ = precision_bytes_
        name = self.value.split(",")[1]
        name_bytes_ = name.encode("utf8")
        bytes_ += name_bytes_
        leftover_byte_space = len(name) + 1
        while (
            leftover_byte_space < 8
        ):  # add null bytes in remaining empty space
            bytes_ += struct.pack("<B", 0)
            leftover_byte_space += 1
        return bytes_

    @classmethod
    def from_bytes(cls, bytes_):
        bytes_len = len(bytes_)
        precision = ""
        name = ""
        for i in range(bytes_len):
            if chr(bytes_[i]).isupper():
                precision = str(bytes_[0])
                name_bytes = bytes_[i:]  # name is all bytes after precision
                for k in range(1, len(name_bytes) + 1):
                    if not chr(bytes_[k]).isupper():
                        name_bytes = name_bytes[
                            : k - 1
                        ]  # name only goes up to the last upper case character
                name = name_bytes.decode("utf8")
                break

        value = precision + "," + name
        return cls(value=value)


class Bytes(Primitive):
    value: bytes

    def __bytes__(self):
        return self.value

    @classmethod
    def from_bytes(cls, bytes_):
        return cls(value=bytes_)


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
        length = Varuint32.from_bytes(bytes_)
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
        length = Varuint32(len(self.values))
        bytes_ += bytes(length)
        for value in self.values:
            bytes_ += bytes(value)
        return bytes_

    def __getitem__(self, index):
        return Array(values=self.values[index], type_=self.type_)


class Name(Primitive):
    # regex = has at least one "non-dot" char
    value: pydantic.constr(
        max_length=13,
        regex=r"^[\.a-z1-5]*[a-z1-5]+[\.a-z1-5]*$|^(?![\s\S])",  # NOQA: F722
    )

    def __eq__(self, other):
        """Equality diregards dots in names."""
        if type(other) != type(self):
            return False
        return self.value.replace(".", "") == other.value.replace(".", "")

    @pydantic.validator("value")
    def last_char_restriction(cls, v):
        if len(v) == 13:
            allowed = {"a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "."}
            if v[-1] not in allowed:
                msg = (
                    "When account name is 13 char long, last char must be "
                    f'in range a-z or ".". "{v[-1]}" found.'
                )
                raise ValueError(msg)
        return v

    def __bytes__(self):
        value_int = self.string_to_uint64(self.value)
        uint64 = Uint64(value=value_int)
        return bytes(uint64)

    @classmethod
    def from_bytes(cls, bytes_):
        uint64 = Uint64.from_bytes(bytes_)
        value_str = cls.uint64_to_string(uint64.value, strip_dots=True)
        return cls(value=value_str)

    @classmethod
    def char_to_symbol(cls, c):
        if c >= ord("a") and c <= ord("z"):
            return (c - ord("a")) + 6
        if c >= ord("1") and c <= ord("5"):
            return (c - ord("1")) + 1
        return 0

    @classmethod
    def string_to_uint64(cls, s):
        if len(s) > 13:
            raise Exception("invalid string length")
        name = 0
        i = 0
        while i < min(len(s), 12):
            name |= (cls.char_to_symbol(ord(s[i])) & 0x1F) << (
                64 - 5 * (i + 1)
            )
            i += 1
        if len(s) == 13:
            name |= cls.char_to_symbol(ord(s[12])) & 0x0F
        return name

    @classmethod
    def uint64_to_string(cls, n, strip_dots=False):
        charmap = ".12345abcdefghijklmnopqrstuvwxyz"
        s = bytearray(13 * b".")
        tmp = n
        for i in range(13):
            c = charmap[tmp & (0x0F if i == 0 else 0x1F)]
            s[12 - i] = ord(c)
            tmp >>= 4 if i == 0 else 5

        s = s.decode("utf8")
        if strip_dots:
            s = s.strip(".")
        return s


class Int8(Primitive):
    value: pydantic.conint(ge=-128, lt=128)

    def __bytes__(self):
        return struct.pack("<b", self.value)

    @classmethod
    def from_bytes(cls, bytes_):
        struct_tuple = struct.unpack("<b", bytes_[:1])
        value = struct_tuple[0]
        return cls(value=value)


class Uint8(Primitive):
    value: pydantic.conint(ge=0, lt=256)  # 2 ** 8

    def __bytes__(self):
        return struct.pack("<B", self.value)

    @classmethod
    def from_bytes(cls, bytes_):
        struct_tuple = struct.unpack("<B", bytes_[:1])
        value = struct_tuple[0]
        return cls(value=value)


class Uint16(Primitive):
    value: pydantic.conint(ge=0, lt=65536)  # 2 ** 16

    def __bytes__(self):
        return struct.pack("<H", self.value)

    @classmethod
    def from_bytes(cls, bytes_):
        struct_tuple = struct.unpack("<H", bytes_[:2])
        value = struct_tuple[0]
        return cls(value=value)


class Uint32(Primitive):
    value: pydantic.conint(ge=0, lt=4294967296)  # 2 ** 32

    def __bytes__(self):
        return struct.pack("<I", self.value)

    @classmethod
    def from_bytes(cls, bytes_):
        struct_tuple = struct.unpack("<I", bytes_[:4])
        value = struct_tuple[0]
        return cls(value=value)


class Uint64(Primitive):
    value: pydantic.conint(ge=0, lt=18446744073709551616)  # 2 ** 64

    def __bytes__(self):
        return struct.pack("<Q", self.value)

    @classmethod
    def from_bytes(cls, bytes_):
        struct_tuple = struct.unpack("<Q", bytes_)
        value = struct_tuple[0]
        return cls(value=value)


class Varuint32(Primitive):
    value: pydantic.conint(ge=0, le=20989371979)

    def __bytes__(self):
        bytes_ = b""
        val = self.value
        while True:
            b = val & 0x7F
            val >>= 7
            b |= (val > 0) << 7
            uint8 = Uint8(value=b)
            bytes_ += bytes(uint8)
            if not val:
                break
        return bytes_

    @classmethod
    def from_bytes(cls, bytes_):
        offset = 0
        value = 0
        for n, byte in enumerate(bytes_):
            partial_value = byte & 0x7F  # only the 7 first bits matter
            partial_value_offset = partial_value << offset
            value |= partial_value_offset
            offset += 7
            if n >= 8:
                break
            if not byte & 0x80:  # first bit (carry) off
                break
        return cls(value=value)


class Abi(Composte):
    comment: String
    version: String
    types: Array
    structs: Array
    actions: Array
    tables: Array
    kv_tables: Array
    ricardian_clauses: Array
    variants: Array
    action_results: Array

    @classmethod
    def from_dict(cls, d: dict, /):
        comment = String(d.get("____comment", ""))
        version = String(d["version"])
        types = Array(type_=String, values=d["types"])
        structs = Array(type_=_AbiStructs, values=d["structs"])
        structs = Array(type_=_AbiStructs, values=[])
        actions = Array(type_=_AbiAction, values=d["actions"])
        tables = Array(type_=_AbiTable, values=d["tables"])
        kv_tables = Array(type_=String, values=[])
        ricardian_clauses = Array(type_=String, values=[])
        variants = Array(type_=String, values=[])
        action_results = Array(type_=String, values=[])
        o = cls(
            comment=comment,
            version=version,
            types=types,
            structs=structs,
            actions=actions,
            tables=tables,
            kv_tables=kv_tables,
            ricardian_clauses=ricardian_clauses,
            variants=variants,
            action_results=action_results,
        )
        return o

    @classmethod
    def from_file(cls, file: Path, *, extension: str = ".abi"):
        """Create a abi object from a .abi or from a zipped file."""
        file_contents_bin = _load_bin_from_file(file=file, extension=extension)
        file_contents_dict = json.loads(file_contents_bin)
        abi_obj = cls.from_dict(file_contents_dict)
        return abi_obj

    def import_abi_data(self, json_data):
        abi_dict = AbiSchema(**json_data)

        version = String(abi_dict.version)
        type_list = []
        struct_list = []
        action_list = []
        table_list = []

        for value in abi_dict.types:
            type_list.append(AbiType(value))
        for value in abi_dict.structs:
            struct_list.append(AbiStruct(value))
        for value in abi_dict.actions:
            action_list.append(
                AbiAction(
                    name=Name(value["name"]),
                    type=String(value["type"]),
                    ricardian_contract=String(value["ricardian_contract"]),
                )
            )
        for value in abi_dict.tables:
            table_list.append(AbiTable(value))

        types = (
            Array(type_=AbiType, values=type_list) if type_list else String("")
        )
        structs = (
            Array(type_=AbiStruct, values=struct_list)
            if struct_list
            else String("")
        )
        actions = (
            Array(type_=AbiAction, values=action_list)
            if action_list
            else String("")
        )
        tables = (
            Array(type_=AbiTable, values=table_list)
            if table_list
            else String("")
        )
        ricardian_clauses = String("")
        error_messages = String("")
        abi_extensions = String("")
        variants = String("")
        action_results = String("")
        kv_tables = String("")

        abi_components = [
            version,
            types,
            structs,
            actions,
            tables,
            ricardian_clauses,
            error_messages,
            abi_extensions,
            variants,
            action_results,
            kv_tables,
        ]

        return abi_components

    def to_hex(self):
        abi_components = self.import_abi_data(self.value)
        abi_bytes = b""
        for value in abi_components:
            abi_bytes += bytes(value)

        return _bin_to_hex(abi_bytes)

    def __bytes__(self):
        hexcode = self.to_hex()
        uint8_array = _hex_to_uint8_array(hexcode)

        return bytes(uint8_array)

    @classmethod
    def from_bytes(cls, bytes_):
        ...


class _AbiStructsField(Composte):
    name: String
    type_: String

    @classmethod
    def from_dict(cls, d: dict, /):
        name = String(d["name"])
        type_ = String(d["type"])
        return cls(name=name, type_=type_)

    @classmethod
    def from_bytes(cls, bytes_):
        name = String.from_bytes(bytes_)
        type_ = String.from_bytes(bytes_[len(name) :])  # NOQA: E203
        return cls(name=name, type_=type_)

    def __bytes__(self):
        return bytes(self.name) + bytes(self.type_)


class _AbiStructs(Composte):
    name: String
    base: String
    fields: Array  # an array of _AbiStructsField

    @classmethod
    def from_dict(cls, d: dict, /):
        name = String(d["name"])
        base = String(d["base"])
        fields = Array(values=d["fields"], type_=_AbiStructsField)
        o = cls(name=name, base=base, fields=fields)
        return o

    @classmethod
    def from_bytes(cls, bytes_):
        ...

    def __bytes__(self):
        ...


class _AbiAction(Composte):
    name: String
    type_: String
    ricardian_contract: String

    @classmethod
    def from_dict(cls, d: dict, /):
        name = String(d["name"])
        type_ = String(d["type"])
        ric_contract = String(d["ricardian_contract"])
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
    name: Name
    index_type: String
    key_names: Array
    key_types: Array
    type_: String

    @classmethod
    def from_dict(cls, d: dict, /):
        name = Name(d["name"])
        index_type = String(d["index_type"])
        key_names = Array(type_=String, values=[])
        key_types = Array(type_=String, values=[])
        type_ = String(d["type"])
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
        uint8_array = Array.from_bytes(bytes_=bytes_, type_=Uint8)
        uint8_list = uint8_array.values
        hexcode = _uint8_list_to_hex(uint8_list)
        value = _hex_to_bin(hexcode)
        return cls(value=value)


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

    uint8_array = Array(type_=Uint8, values=uint8_values)
    return uint8_array


def _uint8_list_to_hex(uint8_list: list) -> str:
    hexcode = ""
    for int8 in uint8_list:
        hexcode += ("00" + str(format(int8.value, "x")))[-2:]
    return hexcode


def _hex_to_bin(hexcode: str) -> bytes:
    return binascii.unhexlify(hexcode.encode("utf-8"))


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
