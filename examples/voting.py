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
        # can vote for mutliple producers, so value is of type array
        # for Array type, need yo specify type of Array with '_type' and values of array in a list
        value=pyntelope.types.Array(
            type_=pyntelope.types.Name, values=["eosiodetroit"]
        ),
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
