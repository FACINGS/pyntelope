"""type tests."""

import datetime as dt
import json
import os
from pathlib import Path

import pydantic
import pytest

from pyntelope import types
from pyntelope.types.compostes import _AbiType

from .contracts.valid import eosio_token
from .contracts.valid import simplecontract as valid_contract


def load_dict_from_path(path: str):
    filename = Path().resolve() / Path(path)
    with open(filename, "rb") as f:
        return json.load(f)


values = [
    (types.Bool, True, b"\x01"),
    (types.Bool, False, b"\x00"),
    (types.Int8, -128, b"\x80"),
    (types.Int8, -127, b"\x81"),
    (types.Int8, -1, b"\xFF"),
    (types.Int8, 0, b"\x00"),
    (types.Int8, 1, b"\x01"),
    (types.Int8, 127, b"\x7F"),
    (types.Int16, -32768, b"\x00\x80"),
    (types.Int16, -32767, b"\x01\x80"),
    (types.Int16, -1, b"\xff\xff"),
    (types.Int16, 0, b"\x00\x00"),
    (types.Int16, 1, b"\x01\x00"),
    (types.Int16, 32767, b"\xff\x7f"),
    (types.Int32, -2147483648, b"\x00\x00\x00\x80"),
    (types.Int32, -2147483647, b"\x01\x00\x00\x80"),
    (types.Int32, -1, b"\xff\xff\xff\xff"),
    (types.Int32, 0, b"\x00\x00\x00\x00"),
    (types.Int32, 1, b"\x01\x00\x00\x00"),
    (types.Int32, 2147483647, b"\xff\xff\xff\x7f"),
    (types.Int64, -9223372036854775808, b"\x00\x00\x00\x00\x00\x00\x00\x80"),
    (types.Int64, -9223372036854775807, b"\x01\x00\x00\x00\x00\x00\x00\x80"),
    (types.Int64, -1, b"\xff\xff\xff\xff\xff\xff\xff\xff"),
    (types.Int64, 0, b"\x00\x00\x00\x00\x00\x00\x00\x00"),
    (types.Int64, 1, b"\x01\x00\x00\x00\x00\x00\x00\x00"),
    (types.Int64, 9223372036854775807, b"\xff\xff\xff\xff\xff\xff\xff\x7f"),
    (types.Float32, 0, b"\x00\x00\x00\x00"),
    (types.Float32, 0.1, b"\xcd\xcc\xcc="),
    (types.Float32, 0.10, b"\xcd\xcc\xcc="),
    (types.Float32, 0.100, b"\xcd\xcc\xcc="),
    (types.Float32, 0.00001, b"\xac\xc5'7"),
    (types.Float32, 0.3, b"\x9a\x99\x99>"),
    (types.Float32, 1, b"\x00\x00\x80?"),
    (types.Float32, 1.0, b"\x00\x00\x80?"),
    (types.Float32, 10, b"\x00\x00 A"),
    (types.Float32, 1e15, b"\xa9_cX"),
    (types.Float32, 1.15e15, b"h\xbd\x82X"),
    (types.Float32, -0, b"\x00\x00\x00\x00"),
    (types.Float32, -0.1, b"\xcd\xcc\xcc\xbd"),
    (types.Float32, -0.10, b"\xcd\xcc\xcc\xbd"),
    (types.Float32, -0.100, b"\xcd\xcc\xcc\xbd"),
    (types.Float32, -0.00001, b"\xac\xc5'\xb7"),
    (types.Float32, -0.3, b"\x9a\x99\x99\xbe"),
    (types.Float32, -1, b"\x00\x00\x80\xbf"),
    (types.Float32, -1.0, b"\x00\x00\x80\xbf"),
    (types.Float32, -10, b"\x00\x00 \xc1"),
    (types.Float32, -1e15, b"\xa9_c\xd8"),
    (types.Float32, -1.15e15, b"h\xbd\x82\xd8"),
    (types.Float64, 0, b"\x00\x00\x00\x00\x00\x00\x00\x00"),
    (types.Float64, 0.1, b"\x9a\x99\x99\x99\x99\x99\xb9?"),
    (types.Float64, 0.10, b"\x9a\x99\x99\x99\x99\x99\xb9?"),
    (types.Float64, 0.100, b"\x9a\x99\x99\x99\x99\x99\xb9?"),
    (types.Float64, 0.00001, b"\xf1h\xe3\x88\xb5\xf8\xe4>"),
    (types.Float64, 0.3, b"333333\xd3?"),
    (types.Float64, 1, b"\x00\x00\x00\x00\x00\x00\xf0?"),
    (types.Float64, 1.0, b"\x00\x00\x00\x00\x00\x00\xf0?"),
    (types.Float64, 10, b"\x00\x00\x00\x00\x00\x00$@"),
    (types.Float64, 1e15, b"\x00\x004&\xf5k\x0cC"),
    (types.Float64, 1.15e15, b"\x00\x80\xf7\xf5\xacW\x10C"),
    (types.Float64, -0, b"\x00\x00\x00\x00\x00\x00\x00\x00"),
    (types.Float64, -0.1, b"\x9a\x99\x99\x99\x99\x99\xb9\xbf"),
    (types.Float64, -0.10, b"\x9a\x99\x99\x99\x99\x99\xb9\xbf"),
    (types.Float64, -0.100, b"\x9a\x99\x99\x99\x99\x99\xb9\xbf"),
    (types.Float64, -0.00001, b"\xf1h\xe3\x88\xb5\xf8\xe4\xbe"),
    (types.Float64, -0.3, b"333333\xd3\xbf"),
    (types.Float64, -1, b"\x00\x00\x00\x00\x00\x00\xf0\xbf"),
    (types.Float64, -1.0, b"\x00\x00\x00\x00\x00\x00\xf0\xbf"),
    (types.Float64, -10, b"\x00\x00\x00\x00\x00\x00$\xc0"),
    (types.Float64, -1e15, b"\x00\x004&\xf5k\x0c\xc3"),
    (types.Float64, -1.15e15, b"\x00\x80\xf7\xf5\xacW\x10\xc3"),
    (types.Uint8, 0, b"\x00"),
    (types.Uint8, 1, b"\x01"),
    (types.Uint8, 254, b"\xFE"),
    (types.Uint8, 255, b"\xFF"),
    (types.Uint16, 0, b"\x00\x00"),
    (types.Uint16, 1, b"\x01\x00"),
    (types.Uint16, 2**16 - 2, b"\xFE\xFF"),
    (types.Uint16, 2**16 - 1, b"\xFF\xFF"),
    (types.Uint32, 0, b"\x00\x00\x00\x00"),
    (types.Uint32, 1, b"\x01\x00\x00\x00"),
    (types.Uint32, 10800, b"0*\x00\x00"),
    (types.Uint32, 10800, b"\x30\x2a\x00\x00"),
    (types.Uint32, 123456, b"@\xe2\x01\x00"),
    (types.Uint32, 2**32 - 2, b"\xFE\xFF\xFF\xFF"),
    (types.Uint32, 2**32 - 1, b"\xFF\xFF\xFF\xFF"),
    (types.Uint64, 0, b"\x00\x00\x00\x00\x00\x00\x00\x00"),
    (types.Uint64, 1, b"\x01\x00\x00\x00\x00\x00\x00\x00"),
    (types.Uint64, 2**64 - 2, b"\xFE\xFF\xFF\xFF\xFF\xFF\xFF\xFF"),
    (types.Uint64, 2**64 - 1, b"\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"),
    (types.Varuint32, 0, b"\x00"),
    (types.Varuint32, 1, b"\x01"),
    (types.Varuint32, 3, b"\x03"),
    (types.Varuint32, 2**8 - 1, b"\xFF\x01"),
    (types.Varuint32, 2**8, b"\x80\x02"),
    (types.Varuint32, 2**32 - 1, b"\xFF\xFF\xFF\xFF\x0F"),
    (types.Varuint32, 2**32, b"\x80\x80\x80\x80\x10"),
    (types.Varuint32, 20989371979, b"\xcb\xcc\xc1\x98N"),
    (types.Name, "a", b"\x00\x00\x00\x00\x00\x00\x000"),
    (types.Name, "a.", b"\x00\x00\x00\x00\x00\x00\x000"),
    (types.Name, "b", b"\x00\x00\x00\x00\x00\x00\x008"),
    (types.Name, "zzzzzzzzzzzzj", b"\xff\xff\xff\xff\xff\xff\xff\xff"),
    (types.Name, "kacjndfvdfa", b"\x00\xccJ{\xa5\xf9\x90\x81"),
    (types.Name, "user2", b"\x00\x00\x00\x00\x00q\x15\xd6"),
    (types.Name, "", b"\x00\x00\x00\x00\x00\x00\x00\x00"),
    (types.String, "a", b"\x01a"),
    (types.String, "A", b"\x01A"),
    (types.String, "kcjansdcd", b"\tkcjansdcd"),
    (types.String, "", b"\x00"),
    (types.UnixTimestamp, dt.datetime(1970, 1, 1, 0, 0), b"\x00\x00\x00\x00"),
    (
        types.UnixTimestamp,
        dt.datetime(2040, 12, 31, 23, 59),
        b"\x44\x03\x8D\x85",
    ),
    (
        types.UnixTimestamp,
        dt.datetime(2040, 12, 31, 23, 59, 0),
        b"\x44\x03\x8D\x85",
    ),
    (
        types.UnixTimestamp,
        dt.datetime(2021, 8, 26, 14, 1, 47),
        b"\xCB\x9E\x27\x61",
    ),
    (
        types.UnixTimestamp,
        dt.datetime(2021, 8, 26, 14, 1, 47, 184549),
        b"\xCB\x9E\x27\x61",
    ),
    # minumum amount of characters
    (types.Symbol, "0,W", b"\x00W\x00\x00\x00\x00\x00\x00"),
    # maximum amount of characters
    (types.Symbol, "0,WAXXXXX", b"\x00WAXXXXX"),
    # 1 precision
    (types.Symbol, "1,WAX", b"\x01WAX\x00\x00\x00\x00"),
    # max precision
    (types.Symbol, "16,WAX", b"\x10WAX\x00\x00\x00\x00"),
    (
        types.Asset,
        "99.9 WAX",
        b"\xe7\x03\x00\x00\x00\x00\x00\x00\x01WAX\x00\x00\x00\x00",
    ),
    (
        types.Asset,
        "99 WAX",
        b"c\x00\x00\x00\x00\x00\x00\x00\x00WAX\x00\x00\x00\x00",
    ),
    (
        types.TimePoint,
        dt.datetime(1970, 1, 1, 0, 0),
        b"\x00\x00\x00\x00\x00\x00\x00\x00",
    ),
    (
        types.TimePoint,
        dt.datetime(1970, 1, 1, 0, 0, 0),
        b"\x00\x00\x00\x00\x00\x00\x00\x00",
    ),
    (
        types.TimePoint,
        dt.datetime(1970, 1, 1, 0, 0, 0, 0),
        b"\x00\x00\x00\x00\x00\x00\x00\x00",
    ),
    (
        types.TimePoint,
        dt.datetime(1970, 1, 1, 0, 0, 0, 1000),
        b"\xe8\x03\x00\x00\x00\x00\x00\x00",
    ),
    (
        types.TimePoint,
        dt.datetime(1970, 1, 1, 0, 0, 0, 2000),
        b"\xd0\x07\x00\x00\x00\x00\x00\x00",
    ),
    (
        types.TimePoint,
        dt.datetime(1970, 1, 1, 0, 0, 0, 3000),
        b"\xb8\x0b\x00\x00\x00\x00\x00\x00",
    ),
    (
        types.TimePoint,
        dt.datetime(1970, 1, 1, 0, 0, 0, 4000),
        b"\xa0\x0f\x00\x00\x00\x00\x00\x00",
    ),
    (
        types.TimePoint,
        dt.datetime(1970, 1, 1, 0, 0, 1),
        b"@B\x0f\x00\x00\x00\x00\x00",
    ),
    (
        types.TimePoint,
        dt.datetime(2040, 12, 31, 23, 59),
        b"\x00Y\x14\xef\xd2\xf5\x07\x00",
    ),
    (
        types.TimePoint,
        dt.datetime(2040, 12, 31, 23, 59, 0),
        b"\x00Y\x14\xef\xd2\xf5\x07\x00",
    ),
    (
        types.TimePoint,
        dt.datetime(2021, 8, 26, 14, 1, 47),
        b"\xc0\x08\xbd\xcev\xca\x05\x00",
    ),
]


@pytest.mark.parametrize("class_,input_,expected_output", values)
def test_type_object_to_bytes_serialization(class_, input_, expected_output):
    instance = class_(input_)
    output = bytes(instance)
    assert output == expected_output


@pytest.mark.parametrize("class_,input_,expected_output", values)
def test_type_bytes_to_object_deserialization(class_, input_, expected_output):
    instance = class_(input_)
    bytes_ = bytes(instance)
    new_instance = class_.from_bytes(bytes_)
    assert new_instance == instance


@pytest.mark.parametrize("class_,input_,expected_output", values)
def test_size(class_, input_, expected_output):
    has_len = {
        types.Varuint32,
        types.String,
    }
    if class_ in has_len:
        instance = class_(input_)
        bytes_ = bytes(instance)
        assert len(instance) == len(bytes_)


def test_abi_bytes_to_type_serialization():
    abi_path = valid_contract.path_abi
    bin_path = valid_contract.path_abi_bytes

    abi_obj = types.Abi.from_file(file=abi_path)
    output = bytes(abi_obj)
    expected_output = types.compostes._load_bin_from_file(
        file=bin_path, extension=""
    )

    assert output == expected_output


def test_wasm_bytes_to_type_serialization():
    wasm_path = valid_contract.path_wasm
    bin_path = valid_contract.path_wasm_bytes

    wasm_obj = types.Wasm.from_file(file=wasm_path)
    output = bytes(wasm_obj)
    expected_output = types.compostes._load_bin_from_file(
        file=bin_path, extension=".bin"
    )

    assert output == expected_output


test_serialization = [
    (types.Name, "testname", "hrforxogkfjv"),
    (types.Name, "testname", ""),
    (types.String, "teststring", "hrforxogkfjv"),
    (types.String, "teststring", "Lorem Ipsum " * 10),
    (
        types.String,
        "teststring",
        (
            "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]"
            "^_`abcdefghijklmnopqrstuvwxyz{|}~ "
        ),
    ),
    (types.String, "teststring", ""),
    (types.Int8, "tinteight", -128),
    (types.Int8, "tinteight", -127),
    (types.Int8, "tinteight", 0),
    (types.Int8, "tinteight", 1),
    (types.Int8, "tinteight", 127),
    (types.Int16, "tintsixteen", -32768),
    (types.Int16, "tintsixteen", -32767),
    (types.Int16, "tintsixteen", -1),
    (types.Int16, "tintsixteen", 0),
    (types.Int16, "tintsixteen", 1),
    (types.Int16, "tintsixteen", 32767),
    (types.Int32, "tintthirttwo", -2147483648),
    (types.Int32, "tintthirttwo", -2147483647),
    (types.Int32, "tintthirttwo", -1),
    (types.Int32, "tintthirttwo", 0),
    (types.Int32, "tintthirttwo", 1),
    (types.Int32, "tintthirttwo", 2147483647),
    (types.Int64, "tintsixfour", -9223372036854775808),
    (types.Int64, "tintsixfour", -9223372036854775807),
    (types.Int64, "tintsixfour", -1),
    (types.Int64, "tintsixfour", 0),
    (types.Int64, "tintsixfour", 1),
    (types.Int64, "tintsixfour", 9223372036854775807),
    (types.Float64, "tfltsixfour", 0),
    (types.Float64, "tfltsixfour", 0.1),
    (types.Float64, "tfltsixfour", 0.10),
    (types.Float64, "tfltsixfour", 0.100),
    (types.Float64, "tfltsixfour", 0.00001),
    (types.Float64, "tfltsixfour", 0.3),
    (types.Float64, "tfltsixfour", 1),
    (types.Float64, "tfltsixfour", 1.0),
    (types.Float64, "tfltsixfour", 10),
    (types.Float64, "tfltsixfour", 1e15),
    (types.Float64, "tfltsixfour", 1.15e15),
    (types.Float64, "tfltsixfour", -0),
    (types.Float64, "tfltsixfour", -0.1),
    (types.Float64, "tfltsixfour", -0.10),
    (types.Float64, "tfltsixfour", -0.100),
    (types.Float64, "tfltsixfour", -0.00001),
    (types.Float64, "tfltsixfour", -0.3),
    (types.Float64, "tfltsixfour", -1),
    (types.Float64, "tfltsixfour", -1.0),
    (types.Float64, "tfltsixfour", -10),
    (types.Float64, "tfltsixfour", -1e15),
    (types.Float64, "tfltsixfour", -1.15e15),
    (types.Float32, "tfltthirttwo", 0),
    (types.Float32, "tfltthirttwo", 0.1),
    (types.Float32, "tfltthirttwo", 0.10),
    (types.Float32, "tfltthirttwo", 0.100),
    (types.Float32, "tfltthirttwo", 0.00001),
    (types.Float32, "tfltthirttwo", 0.3),
    (types.Float32, "tfltthirttwo", 1),
    (types.Float32, "tfltthirttwo", 1.0),
    (types.Float32, "tfltthirttwo", 10),
    (types.Float32, "tfltthirttwo", 1e15),
    (types.Float32, "tfltthirttwo", 1.15e15),
    (types.Float32, "tfltthirttwo", -0),
    (types.Float32, "tfltthirttwo", -0.1),
    (types.Float32, "tfltthirttwo", -0.10),
    (types.Float32, "tfltthirttwo", -0.100),
    (types.Float32, "tfltthirttwo", -0.00001),
    (types.Float32, "tfltthirttwo", -0.3),
    (types.Float32, "tfltthirttwo", -1),
    (types.Float32, "tfltthirttwo", -1.0),
    (types.Float32, "tfltthirttwo", -10),
    (types.Float32, "tfltthirttwo", -1e15),
    (types.Float32, "tfltthirttwo", -1.15e15),
    (types.Uint8, "tuinteight", 0),
    (types.Uint8, "tuinteight", 1),
    (types.Uint8, "tuinteight", 254),
    (types.Uint8, "tuinteight", 255),
    (types.Uint16, "tuintsixteen", 0),
    (types.Uint16, "tuintsixteen", 1),
    (types.Uint16, "tuintsixteen", 2),
    (types.Uint16, "tuintsixteen", 2**16 - 2),
    (types.Uint16, "tuintsixteen", 2**16 - 1),
    (types.Uint32, "tuintthirtwo", 0),
    (types.Uint32, "tuintthirtwo", 1),
    (types.Uint32, "tuintthirtwo", 10800),
    (types.Uint32, "tuintthirtwo", 10800),
    (types.Uint32, "tuintthirtwo", 123456),
    (types.Uint32, "tuintthirtwo", 2**32 - 2),
    (types.Uint32, "tuintthirtwo", 2**32 - 1),
    (types.Uint64, "tuintsixfour", 0),
    (types.Uint64, "tuintsixfour", 1),
    (types.Uint64, "tuintsixfour", 2**64 - 2),
    (types.Uint64, "tuintsixfour", 2**64 - 1),
    (types.TimePoint, "ttimepoint", dt.datetime(1970, 1, 1, 0, 0)),
    (types.TimePoint, "ttimepoint", dt.datetime(1970, 1, 1, 0, 0, 0)),
    (types.TimePoint, "ttimepoint", dt.datetime(1970, 1, 1, 0, 0, 0, 0)),
    (types.TimePoint, "ttimepoint", dt.datetime(1970, 1, 1, 0, 0, 0, 1000)),
    (types.TimePoint, "ttimepoint", dt.datetime(1970, 1, 1, 0, 0, 0, 2000)),
    (types.TimePoint, "ttimepoint", dt.datetime(1970, 1, 1, 0, 0, 0, 3000)),
    (types.TimePoint, "ttimepoint", dt.datetime(1970, 1, 1, 0, 0, 0, 4000)),
    (types.TimePoint, "ttimepoint", dt.datetime(1970, 1, 1, 0, 0, 0, 997000)),
    (types.TimePoint, "ttimepoint", dt.datetime(1970, 1, 1, 0, 0, 0, 998000)),
    (types.TimePoint, "ttimepoint", dt.datetime(1970, 1, 1, 0, 0, 0, 999000)),
    (types.TimePoint, "ttimepoint", dt.datetime(1970, 1, 1, 0, 0, 1)),
    (types.TimePoint, "ttimepoint", dt.datetime(2040, 12, 31, 23, 59)),
    (types.TimePoint, "ttimepoint", dt.datetime(2040, 12, 31, 23, 59, 0)),
    (types.TimePoint, "ttimepoint", dt.datetime(2021, 8, 26, 14, 1, 47)),
    (
        types.TimePoint,
        "ttimepoint",
        dt.datetime(2021, 8, 26, 14, 1, 47, 184000),
    ),
]


@pytest.mark.parametrize("class_,action_,value", test_serialization)
def test_pyntelope_serialization_vs_leap_serialization(
    class_, action_, value, net
):
    if class_ == types.TimePoint:
        value = value.isoformat(timespec="microseconds")[:-3]
        print(value)

    nodeos_serialization = net.abi_json_to_bin(
        account_name="user2",
        action=action_,
        json={"var": value},
    )
    local_serialization = bytes(class_(value))
    err_msg = f"{value=}; {nodeos_serialization=}; {local_serialization=}"
    assert nodeos_serialization == local_serialization, err_msg


error_values = [
    (types.Int8, -129),
    (types.Int8, 128),
    (types.Uint8, -1),
    (types.Uint8, 256),
    (types.Uint16, -1),
    (types.Uint16, 2**16),
    (types.Uint32, -1),
    (types.Uint32, 2**32),
    (types.Uint64, -1),
    (types.Uint64, 2**64),
    # (types.Name, ""),
    (types.Name, "A"),
    (types.Name, "z" * 14),
    (types.Name, "á"),
    (types.Name, "."),
    (types.Name, "...."),
    (types.Name, "zzzzzzzzzzzzz"),
    (types.Name, "aaaaaaaaaaaaz"),
    (types.Name, "............z"),
    (types.Varuint32, -1),
    (types.Varuint32, 20989371980),
    # utf 2 byte char
    (types.String, "µ"),
    (types.String, "aµ"),
    (types.String, "µa"),
    (types.String, "aµa"),
    # utf 3 byte char
    (types.String, "ࢠ"),
    (types.String, "aࢠ"),
    (types.String, "ࢠa"),
    # utf 4 byte char
    (types.String, "𒀀"),
    (types.String, "a𒀀"),
    (types.String, "𒀀a"),
    # additional utf 4 byte char
    (types.String, "🤎"),
    (types.String, "a🤎"),
    (types.String, "🤎a"),
    (types.Symbol, "0,WAXXXXXX"),
    (types.Symbol, "0,"),
    (types.Symbol, "0, "),
    (types.Symbol, ","),
    (types.Symbol, "17,WAX"),
    (types.Symbol, "-1,WAX"),
    (types.Asset, "1WAX"),
    (types.Asset, "1 1 WAX"),
    (types.Asset, "WAX"),
    (types.Asset, "-1 WAX"),
    (types.Asset, str(2**64) + " WAX"),
    (types.Asset, "1 WAXXXXXX"),
    (types.Asset, "99 "),
    (types.Asset, "99"),
    (types.Asset, "99. WAXXXXXX"),
    (types.Asset, "99."),
    (types.TimePoint, dt.datetime(1970, 1, 1, 0, 0, 0, 999997)),
    (types.TimePoint, dt.datetime(1970, 1, 1, 0, 0, 0, 999998)),
    (types.TimePoint, dt.datetime(1970, 1, 1, 0, 0, 0, 999999)),
    (types.TimePoint, dt.datetime(2021, 8, 26, 14, 1, 47, 184549)),
]


@pytest.mark.parametrize("class_,input_", error_values)
def test_type_validation_errors(class_, input_):
    with pytest.raises(pydantic.ValidationError):
        class_(input_)


array_values = [
    (
        types.Int8,
        [-128, -127, 126, 127],
        b"\x04\x80\x81\x7E\x7F",
    ),
    (
        types.Varuint32,
        [0, 2**8, 2**16, 2**4],
        b"\x04\x00\x80\x02\x80\x80\x04\x10",
    ),
    (
        _AbiType,
        [
            dict(new_type_name="a", type="b"),
            dict(new_type_name="c", type="d"),
        ],
        b"\x02\x01a\x01b\x01c\x01d",
    ),
]


@pytest.mark.parametrize("type_,input_,expected_output", array_values)
def test_array_to_bytes(type_, input_, expected_output):
    array = types.Array.from_dict(input_, type_=type_)
    output = bytes(array)
    assert output == expected_output


@pytest.mark.parametrize("type_,input_,expected_output", array_values)
def test_bytes_to_array(type_, input_, expected_output):
    array = types.Array.from_dict(input_, type_=type_)
    bytes_ = bytes(array)
    array_from_bytes = types.Array.from_bytes(bytes_, type_=type_)
    assert array_from_bytes == array, f"{array=}; {array_from_bytes=}"


@pytest.mark.parametrize("type_,input_,bytes_", array_values)
def test_array_to_dict(type_, input_, bytes_):
    array_obj = types.Array.from_dict(input_, type_=type_)
    dict_from_array = array_obj.to_dict()
    assert dict_from_array == input_


@pytest.mark.parametrize("class_,input_", error_values)
def test_array_validation_errors(class_, input_):
    if type(input_) in {int, float, dt.datetime}:
        input_ = (input_,)
    with pytest.raises(pydantic.ValidationError):
        types.Array(type_=class_, values=tuple(input_))


def test_array_initialized_with_list_and_tuples_returns_the_same_result():
    arr1 = types.Array.from_dict([1, 2, 3], type_=types.Int8)
    arr2 = types.Array.from_dict((1, 2, 3), type_=types.Int8)
    assert hash(arr1) == hash(arr2)


def test_array_initialized_with_list_and_range_returns_the_same_result():
    arr1 = types.Array.from_dict([1, 2, 3], type_=types.Int8)
    arr2 = types.Array.from_dict(range(1, 4), type_=types.Int8)
    assert hash(arr1) == hash(arr2)


def test_array_initialized_with_list_and_string_returns_the_same_result():
    arr1 = types.Array.from_dict(["a", "b", "c"], type_=types.Name)
    arr2 = types.Array.from_dict("abc", type_=types.Name)
    assert hash(arr1) == hash(arr2)


def test_array_elements_are_immutable_directly():
    arr = types.Array.from_dict([1, 2, 3], type_=types.Int8)
    with pytest.raises(TypeError):
        arr[1] = 2


def test_array_elements_are_immutable_when_try_to_mutate_value():
    arr = types.Array.from_dict([1, 2, 3], type_=types.Int8)
    with pytest.raises(TypeError):
        arr.values[1] = 2


def test_antelope_type_cannot_be_instantiated():
    with pytest.raises(TypeError):
        types.AntelopeType()


def test_array_can_be_sliced_1():
    arr_full = types.Array.from_dict(range(10), type_=types.Int8)
    arr_slice = types.Array.from_dict(range(10)[1:4], type_=types.Int8)
    assert arr_full[1:4] == arr_slice


def test_array_can_be_sliced_2():
    arr_full = types.Array.from_dict(range(10), type_=types.Int8)
    arr_slice = types.Array.from_dict(range(10)[8:3:-2], type_=types.Int8)
    assert arr_full[8:3:-2] == arr_slice


def test_wasm_from_zip_file_return_wasm_type():
    path = valid_contract.path_zip
    wasm_obj = types.Wasm.from_file(file=path)
    assert isinstance(wasm_obj, types.Wasm)


def test_wasm_from_wasm_file_return_wasm_type():
    path = valid_contract.path_wasm
    wasm_obj = types.Wasm.from_file(file=path)
    assert isinstance(wasm_obj, types.Wasm)


def test_wasm_from_zip_file_value_matches_expected_bytes():
    path = valid_contract.path_zip
    wasm_obj = types.Wasm.from_file(file=path)
    assert wasm_obj.value == valid_contract.wasm_bytes_


def test_wasm_from_wasm_file_value_matches_expected_bytes():
    path = valid_contract.path_wasm
    wasm_obj = types.Wasm.from_file(file=path)
    assert wasm_obj.value == valid_contract.wasm_bytes_


def test_wasm_from_file_equal_to_wasm_from_bytes():
    file_path = valid_contract.path_zip
    from_bytes = types.Wasm(
        value=types.compostes._load_bin_from_file(
            file=file_path, extension=".wasm"
        )
    )
    from_file = types.Wasm.from_file(file_path)
    assert from_bytes == from_file


def test_wasm_from_file_with_string_and_fullpath_returns_wasm_object():
    path = str(valid_contract.path_zip.absolute())
    wasm_obj = types.Wasm.from_file(file=path)
    assert isinstance(wasm_obj, types.Wasm)


def test_wasm_from_file_with_string_and_relative_path_returns_wasm_object():
    local_path = os.getcwd()
    path = str(valid_contract.path_zip.relative_to(local_path))
    wasm_obj = types.Wasm.from_file(file=path)
    assert isinstance(wasm_obj, types.Wasm)


def test_abi_from_dict_returns_abi_object():
    d = {
        "____comment": "This file",
        "version": "eosio::abi/1.2",
        "types": [],
        "structs": [],
        "actions": [],
        "tables": [],
        "kv_tables": {},
        "ricardian_clauses": [],
        "variants": [],
        "action_results": [],
    }
    abi_obj = types.Abi.from_dict(d)
    assert isinstance(abi_obj, types.Abi)


def test_abi_from_hello_file_return_abi_object():
    abi_obj = types.Abi.from_file(valid_contract.path_abi)
    assert isinstance(abi_obj, types.Abi)


def test_abi_from_eosio_token_file_return_abi_object():
    abi_obj = types.Abi.from_file(eosio_token.path_abi)
    assert isinstance(abi_obj, types.Abi)


def test_abi_from_file_has_comment():
    abi_obj = types.Abi.from_file(valid_contract.path_abi)
    assert hasattr(abi_obj, "comment")


def test_abi_from_bi_file_return_abi_type():
    path = valid_contract.path_abi
    abi_obj = types.Abi.from_file(file=path)
    assert isinstance(abi_obj, types.Abi)


def test_abi_from_dict_equal_to_abi_from_file():
    file_path = valid_contract.path_abi
    from_dict = types.Abi.from_dict(load_dict_from_path(file_path))
    from_file = types.Abi.from_file(file_path)
    assert from_dict == from_file


def test_abi_from_file_with_string_and_fullpath_returns_abi_object():
    path = str(valid_contract.path_abi.absolute())
    abi_obj = types.Abi.from_file(file=path)
    assert isinstance(abi_obj, types.Abi)


def test_abi_from_file_with_string_and_relative_path_returns_abi_object():
    local_path = os.getcwd()
    path = str(valid_contract.path_abi.relative_to(local_path))
    abi_obj = types.Abi.from_file(file=path)
    assert isinstance(abi_obj, types.Abi)
