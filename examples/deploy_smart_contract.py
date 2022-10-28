"""Deploy a smart contract."""

import pyntelope

setcode_data = [
    # data to set wasm file to account me.wam
    pyntelope.Data(
        name="account",
        value=pyntelope.types.Name("me.wam"),
    ),
    pyntelope.Data(
        name="vmtype",
        value=pyntelope.types.Uint8(0),  # almost always set to 0, has to be set
    ),
    pyntelope.Data(
        name="vmversion",
        value=pyntelope.types.Uint8(0),  # almost always set to 0, has to be set
    ),
    pyntelope.Data(
        name="code",  # select "code" field to set a wasm file
        value=pyntelope.types.Wasm.from_file(
            "test_contract/test_contract.zip"
        ),  # path from current directory to wasm file
    ),
]

setabi_data = [
    pyntelope.Data(
        name="account",
        value=pyntelope.types.Name("me.wam"),
    ),
    pyntelope.Data(
        name="abi",  # select "abi" field to set a abi file
        value=pyntelope.types.Abi.from_file(
            "test_contract/test_contract.abi"
        ),  # path from current directory to abi file
    ),
]

auth = pyntelope.Authorization(actor="me.wam", permission="active")

setcode_action = pyntelope.Action(
    account="eosio",
    name="setcode",
    data=setcode_data,
    authorization=[auth],
)

setabi_action = pyntelope.Action(
    account="eosio",
    name="setabi",
    data=setabi_data,
    authorization=[auth],
)

raw_transaction = pyntelope.Transaction(
    actions=[setabi_action, setcode_action]
)

net = pyntelope.WaxTestnet()
linked_transaction = raw_transaction.link(net=net)

key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=key)

resp = signed_transaction.send()
