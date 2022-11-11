"""Vote to a nice blockproducer ;) ."""

import pyntelope

data = [
    # Specifices the voter account
    pyntelope.Data(
        name="voter",
        value=pyntelope.types.Name("me.wam"),
    ),
    # Specifices the proxy (can be empty)
    pyntelope.Data(
        name="proxy",
        value=pyntelope.types.Name(""),
    ),
    # Specifics the producers
    pyntelope.Data(
        name="producers",
        # One can vote for mutliple producers, so value is of type array
        # An Array is what is called a Composte type. It is formed of multiple
        # others pyntelope types.
        # Compostes types instantiation are more verbose.
        value=pyntelope.types.Array.from_dict(
            ["eosiodetroit"], type_=pyntelope.types.Name
        ),
        # If you want to instantiate it directly you'd need to provide a tuple
        # of names:
        # value=pyntelope.types.Array(
        #     values=(pyntelope.types.Name("eosiodetroit")),
        #     type_=pyntelope.types.Name,
        # ),
    ),
]

auth = pyntelope.Authorization(actor="me.wam", permission="active")

action = pyntelope.Action(
    account="eosio",
    name="voteproducer",
    data=data,
    authorization=[auth],
)

raw_transaction = pyntelope.Transaction(actions=[action])

net = pyntelope.WaxTestnet()
linked_transaction = raw_transaction.link(net=net)

key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=key)

resp = signed_transaction.send()
