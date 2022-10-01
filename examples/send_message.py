"""Send a message."""


import pyntelope


data = [
    # Not specifying an account with the "to" field will send the message to the same account sending it in the "from" field
    pyntelope.Data(name="from", value=pyntelope.types.Name("me.wam")),
    pyntelope.Data(
        name="message",
        value=pyntelope.types.String("hello from pyntelope"), # String specified for message type, type must be specificed
    ),
]

auth = pyntelope.Authorization(actor="me.wam", permission="active")

action = pyntelope.Action(
    account="me.wam",
    name="sendmsg",
    data=data,
    authorization=[auth],
)

raw_transaction = pyntelope.Transaction(actions=[action])

net = pyntelope.Local()
linked_transaction = raw_transaction.link(net=net)

key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=key)

resp = signed_transaction.send()
