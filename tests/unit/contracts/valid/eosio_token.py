import os
from pathlib import Path

path = Path(os.path.dirname(__file__))
path_wasm = path / "eosio_token.wasm"
path_abi = path / "eosio_token.abi"
