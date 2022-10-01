"""Buy some ram to some account."""


import pyntelope

data = [
    # in this case the account me.wam is buying ram for itself
    pyntelope.Data(name="payer", value=pyntelope.types.Name("me.wam")),
    pyntelope.Data(name="receiver", value=pyntelope.types.Name("me.wam")),
    pyntelope.Data(
        name="quant", # Selects the 'quant' field in this action, must be a valid field in the action
        value=pyntelope.types.Asset("5.00000000 WAX"), # Asset type must be specified as quant requires the amount and currency type, which Asset includes
    ),
]

auth = pyntelope.Authorization(actor="me.wam", permission="active")

action = pyntelope.Action(
    account="eosio",
    name="buyram",
    data=data,
    authorization=[auth],
)

raw_transaction = pyntelope.Transaction(actions=[action])

net = pyntelope.WaxTestnet()
linked_transaction = raw_transaction.link(net=net)

key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=key)

resp = signed_transaction.send()
