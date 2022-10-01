"""Transfer some WAX to a receiver account."""

import pyntelope

data = [
    # In this case the account me.wam is transferring to account 'reciever'
    pyntelope.Data(name="from", value=pyntelope.types.Name("me.wam")),
    pyntelope.Data(name="to", value=pyntelope.types.Name("receiver")),
    pyntelope.Data(
        name="quantity", # Selects the 'quantity' field in this action, must be a valid field in the action
        value=pyntelope.types.Asset("55.00000000 WAX"), # Asset type must be specified as 'quantity' requires the amount and currency type, which Asset includes
    ),
    pyntelope.Data(
        name="memo", # Selects the 'memo' field in this action, just an extra message with the transfer
        value=pyntelope.types.String("Trying pyntelope"), # String type is used for memo
    ),
]

auth = pyntelope.Authorization(actor="me.wam", permission="active")

action = pyntelope.Action(
    account="eosio.token",
    name="transfer",
    data=data,
    authorization=[auth],
)

raw_transaction = pyntelope.Transaction(actions=[action])

net = pyntelope.WaxTestnet()
linked_transaction = raw_transaction.link(net=net)

key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=key)

resp = signed_transaction.send()
