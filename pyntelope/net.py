"""
Blockchain network main class and its derivatives.

Nodeos api reference:
https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index
"""

import base64
import logging
import typing
from urllib.parse import urljoin

import httpx
import pydantic

from pyntelope import exc
from pyntelope._version import __version__

logger = logging.getLogger(__name__)

DEPRECATION_WARNING = (
    "The abi_bin_to_json and abi_json_to_bin conversion APIs are "
    "both deprecated as of the Leap v3.1 release. "
    "(https://eosnetwork.com/blog/leap-v3-1-release-features/)"
    "They will also be removed from pyntelope in a future version."
)


class Net(pydantic.BaseModel):
    """
    The net hold the connection information with the blockchain network api.
    """  # NOQA: D200

    host: pydantic.AnyHttpUrl
    headers: dict = {}

    def _request(
        self,
        *,
        endpoint: str,
        payload: typing.Optional[dict] = dict(),
        verb: str = "POST",
    ):
        url = urljoin(self.host, endpoint)

        headers = {
            "user-agent": f"pyntelope/{__version__}",
            "content-type": "application/json",
        }
        headers.update(self.headers)

        try:
            resp = httpx.post(url, json=payload, headers=headers)
        except (
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.WriteError,
        ) as e:
            raise exc.ConnectionError(
                response=None, url=url, payload=payload, error=e
            )

        if resp.status_code > 299 and resp.status_code != 500:
            raise exc.ConnectionError(
                response=resp, url=url, payload=payload, error=None
            )

        return resp.json()

    def abi_bin_to_json(
        self, *, account_name: str, action: str, bytes: dict
    ) -> dict:
        logger.warning(DEPRECATION_WARNING)
        endpoint = "/v1/chain/abi_bin_to_json"
        payload = dict(code=account_name, action=action, binargs=bytes.hex())
        data = self._request(endpoint=endpoint, payload=payload)
        return data["args"]

    def abi_json_to_bin(
        self, *, account_name: str, action: str, json: dict
    ) -> bytes:
        """
        Return a dict containing the serialized action data.

        https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index#operation/abi_json_to_bin
        """
        logger.warning(DEPRECATION_WARNING)
        endpoint = "/v1/chain/abi_json_to_bin"
        payload = dict(code=account_name, action=action, args=json)
        data = self._request(endpoint=endpoint, payload=payload)
        if "binargs" not in data:
            return data
        hex_ = data["binargs"]
        bytes_ = bytes.fromhex(hex_)
        return bytes_

    def get_raw_code_and_abi(self, *, account_name: str) -> bytes:
        """
        Retrieve raw code and ABI for a contract based on account name.

        https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index#operation/get_raw_code_and_abi
        """
        endpoint = "/v1/chain/get_raw_code_and_abi"
        payload = dict({"account_name": account_name})
        data = self._request(endpoint=endpoint, payload=payload)

        data["abi"] = base64.b64decode(data["abi"])
        data["wasm"] = base64.b64decode(data["wasm"])
        return data

    def get_info(self):
        endpoint = "/v1/chain/get_info"
        data = self._request(endpoint=endpoint)
        return data

    def get_account(self, *, account_name: str):
        """
        Return an account information.

        If no account is found, then raises an connection error
        https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index#operation/get_account
        """
        endpoint = "/v1/chain/get_account"
        payload = dict(account_name=account_name)
        data = self._request(endpoint=endpoint, payload=payload)
        return data

    def get_abi(self, *, account_name: str):
        """
        Retrieve the ABI for a contract based on its account name.

        https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index#operation/get_abi
        """
        endpoint = "/v1/chain/get_abi"
        payload = dict(account_name=account_name)
        data = self._request(endpoint=endpoint, payload=payload)
        if len(data) == 1:
            return None
        return data

    def get_block(self, *, block_num_or_id: str):
        """
        Return various details about a specific block on the blockchain.

        https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index#operation/get_block
        """
        endpoint = "/v1/chain/get_block"
        payload = dict(block_num_or_id=block_num_or_id)
        data = self._request(endpoint=endpoint, payload=payload)
        return data

    def get_block_info(self, *, block_num: str):
        """
        Return a fixed-size smaller subset of the block data.

        Similar to get_block
        https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index#operation/get_block_info
        """
        endpoint = "/v1/chain/get_block_info"
        payload = dict(block_num=block_num)
        data = self._request(endpoint=endpoint, payload=payload)
        return data

    def get_table_by_scope(
        self,
        code: str,
        table: str = None,
        lower_bound: str = None,
        upper_bound: str = None,
        limit: int = None,
        reverse: bool = None,
        show_payer: bool = None,
    ):
        """
        Return a dict with all tables and their scope.

        Similar to get_table_by_scope
        https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index#operation/get_table_by_scope
        """
        endpoint = "/v1/chain/get_table_by_scope"
        payload = dict(
            code=code,
            table=table,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            limit=limit,
            reverse=reverse,
            show_payer=show_payer,
        )
        for k in list(payload.keys()):
            if payload[k] is None:
                del payload[k]
        data = self._request(endpoint=endpoint, payload=payload)
        return data

    def get_table_rows(
        self,
        code: str,
        table: str,
        scope: str,
        json: bool = True,
        index_position: str = None,
        key_type: str = None,
        encode_type: str = None,
        lower_bound: str = None,
        upper_bound: str = None,
        limit: int = 1000,
        reverse: int = None,
        show_payer: int = None,
        full: bool = False,
    ):
        """
        Return a list with the rows in the table.

        Similar to get_table_rows
        https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index#operation/get_table_rows

        Parameters:
        -----------
        json: bool = True
            Get the response as json
        full: bool = True
            Get the full table.
            Requires multiple requests to be made.
            The maximum number of requests made is 1000.
        """
        endpoint = "/v1/chain/get_table_rows"

        payload = dict(
            code=code,
            table=table,
            scope=scope,
            json=json,
            index_position=index_position,
            key_type=key_type,
            encode_type=encode_type,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            limit=limit,
            reverse=reverse,
            show_payer=show_payer,
        )
        payload = {k: v for k, v in payload.items() if v is not None}

        rows = []
        for _ in range(1000):
            logger.debug(f"Get data with {lower_bound=}")
            data = self._request(endpoint=endpoint, payload=payload)
            if "rows" not in data:
                return data
            rows += data["rows"]

            if not full or not data.get("more"):
                break

            lower_bound = data["next_key"]
            payload["lower_bound"] = lower_bound
        else:
            raise ValueError("Too many requests (>1000) for table")

        return rows

    def push_transaction(
        self,
        *,
        transaction: object,
        compression: bool = False,
        packed_context_free_data: str = "",
    ):
        """
        Send a transaction to the blockchain.

        https://developers.eos.io/manuals/eos/latest/nodeos/plugins/chain_api_plugin/api-reference/index#operation/push_transaction
        """
        endpoint = "/v1/chain/push_transaction"
        payload = dict(
            signatures=transaction.signatures,
            compression=compression,
            packed_context_free_data=packed_context_free_data,
            packed_trx=transaction.pack(),
        )
        data = self._request(endpoint=endpoint, payload=payload)
        return data


class WaxTestnet(Net):
    host: pydantic.HttpUrl = "https://testnet.wax.detroitledger.tech"


class WaxMainnet(Net):
    host: pydantic.HttpUrl = "https://api.wax.detroitledger.tech"


class EosMainnet(Net):
    host: pydantic.HttpUrl = "https://api.eos.detroitledger.tech"


class KylinTestnet(Net):
    host: pydantic.HttpUrl = "https://kylin.eossweden.org"


class Jungle3Testnet(Net):
    host: pydantic.HttpUrl = "https://jungle3.eossweden.org"


class Jungle4Testnet(Net):
    host: pydantic.HttpUrl = "https://jungle4.api.eosnation.io"


class TelosMainnet(Net):
    host: pydantic.HttpUrl = "https://telos.caleos.io/"


class TelosTestnet(Net):
    host: pydantic.HttpUrl = "https://testnet.telos.detroitledger.tech"


class ProtonMainnet(Net):
    host: pydantic.HttpUrl = "https://proton.cryptolions.io"


class ProtonTestnet(Net):
    host: pydantic.HttpUrl = "https://testnet.protonchain.com"


class UosMainnet(Net):
    host: pydantic.HttpUrl = "https://uos.eosusa.news"


class FioMainnet(Net):
    host: pydantic.HttpUrl = "https://fio.cryptolions.io"


class Local(Net):
    host: pydantic.HttpUrl = "http://127.0.0.1:8888"


__all__ = [
    "Net",
    "EosMainnet",
    "KylinTestnet",
    "Jungle3Testnet",
    "Jungle4Testnet",
    "TelosMainnet",
    "TelosTestnet",
    "ProtonMainnet",
    "ProtonTestnet",
    "UosMainnet",
    "FioMainnet",
    "WaxTestnet",
    "WaxMainnet",
    "Local",
]
