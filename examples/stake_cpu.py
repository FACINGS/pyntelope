"""Stake cpu / delegate bandwitdh to an account."""

import pyntelope

data = [
    # In this case the account me.wam is staking cpu for itself
    pyntelope.Data(name="from", value=pyntelope.types.Name("me.wam")),
    pyntelope.Data(name="receiver", value=pyntelope.types.Name("me.wam")),
    pyntelope.Data(
        name="stake_cpu_quantity", # Selects the 'stake_cpu_quantity' field in this action to stake cpu, any fields must exist in the action to be selected
        value=pyntelope.types.Asset("15.00000000 WAX"), # Asset type must be specified as 'stake_cpu_quantity' requires the amount and currency type, which Asset includes
    ),
    pyntelope.Data(
        name="stake_net_quantity", # Selects the 'stake_net_quantity' field in this action to stake net
        value=pyntelope.types.Asset("30.00000000 WAX"), # Asset type must be specified as 'stake_net_quantity' requires the amount and currency type, which Asset includes
    ),
    pyntelope.Data(
        name="transfer", # Selects the 'transfer' field in this action to stake cpu
        value=pyntelope.types.Bool(False), # Bool type used to indicate transfer
    ),
]

auth = pyntelope.Authorization(actor="me.wam", permission="active")

action = pyntelope.Action(
    account="eosio",
    name="delegatebw",
    data=data,
    authorization=[auth],
)

raw_transaction = pyntelope.Transaction(actions=[action])

net = pyntelope.WaxTestnet()
linked_transaction = raw_transaction.link(net=net)

key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=key)

resp = signed_transaction.send()
