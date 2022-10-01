"""Run a `runjob` action."""


import pyntelope


data = [
    pyntelope.Data(
        name="worker",
        value=pyntelope.types.Name("open.facings"),
    ),
    pyntelope.Data(
        name="nonce",
        value=pyntelope.types.Uint64(123),
    ),
]

auth = pyntelope.Authorization(actor="youraccount", permission="active")

action = pyntelope.Action(
    account="open.facings",
    name="runjobs",
    data=data,
    authorization=[auth],
)

raw_transaction = pyntelope.Transaction(actions=[action])

net = pyntelope.WaxTestnet()
linked_transaction = raw_transaction.link(net=net)

key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=key)

resp = signed_transaction.send()
