<div align="center">
    
<p align="center">
  <img width="600" src="https://miro.medium.com/max/1400/1*5KEvJB1UBBsk_1ZTBtJfJA.png">
</p>
    
*Minimalist python library to interact with antelope blockchain networks*
 
![Test](https://github.com/FACINGS/pyntelope/actions/workflows/main_workflow.yml/badge.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyntelope)
![version](https://img.shields.io/pypi/v/pyntelope)
![GitHub repo size](https://img.shields.io/github/repo-size/facings/pyntelope)
![GitHub last commit](https://img.shields.io/github/last-commit/facings/pyntelope)

</div>

# What is it?
**pyntelope** is a python library to interact with Antelope blockchains.  
Its main focus are server side applications.  
This library is heavily influenced by [µEOSIO](https://github.com/EOSArgentina/ueosio). Many thanks to them for the astonishing job!  


# Main features
- Send transactions
Its main usage today is to send transactions to the blockchain
- Statically typed
This library enforces and verifies types and values.
- Serialization
**pyntelope** serializes the transaction before sending to the blockchain. 
- Paralellization
Although python has the [GIL](https://realpython.com/python-gil/) we try to make as easier as possible to paralellize the jobs.  
All data is as immutable and all functions are as pure as we can make them.  


# Stability
This work is in alpha version. That means that we make constant breaking changes to its api.  
Also there are known (and, of course unknown) bugs and various limitations.  
Given that, we at [FACINGS](https://facings.io/) have been using this library in production for over an year now.  
However we'd advise for you to fix its version when deploying to prod.  


# Using
Just `pip install pyntelope` and play around.  
(we don't support, and have no plans to support [conda](https://docs.conda.io/en/latest/))  
Rather then starting with long docs, just a simple example:  


## Use Send Message action
```python
import pyntelope


print("Create Transaction")
data=[
    pyntelope.Data(
        name="from",
        value=pyntelope.types.Name("me.wam"), 
    ),
    pyntelope.Data(
        name="message",
         value=pyntelope.types.String("hello from pyntelope"),
    ),
]

auth = pyntelope.Authorization(actor="me.wam", permission="active")

action = pyntelope.Action(
    account="me.wam", # this is the contract account
    name="sendmsg", # this is the action name
    data=data,
    authorization=[auth],
)

raw_transaction = pyntelope.Transaction(actions=[action])

print("Link transaction to the network")
net = pyntelope.WaxTestnet()  # this is an alias for a testnet node
# notice that pyntelope returns a new object instead of change in place
linked_transaction = raw_transaction.link(net=net)


print("Sign transaction")
key = "a_very_secret_key"
signed_transaction = linked_transaction.sign(key=key)


print("Send")
resp = signed_transaction.send()

print("Printing the response")
resp_fmt = json.dumps(resp, indent=4)
print(f"Response:\n{resp_fmt}")
```

There are some other examples [here](./examples)


# Known bugs
### multi-byte utf-8 characters can not be serialized
- Serialization of multi-byte utf-8 characters is somewhat unpredictable in the current implementation, therfore any String input containing multi-utf8 byte characters will be blocked for the time being.


# Contributing
All contributions, bug reports, bug fixes, documentation improvements, enhancements, and ideas are welcome.  
If you find a bug, just open a issue with a tag "BUG".  
If you want to request a new feature, open an issue with a tag "ENH" (for enhancement).  
If you feel like that our docs could be better, please open one with a tag "DOC".  
Although we have the next few steps already planned, we are happy to receive the community feedback to see where to go from there.  


### Development
If you want to develop for **pyntelope**, here are some tips for a local development environment.
We'll be more then happy to receive PRs from the community.
Also we're going full [Black](https://black.readthedocs.io/en/stable/) and enforcing [pydocstyle](http://www.pydocstyle.org/en/stable/) and [isort](https://pypi.org/project/isort/) (with the limitations described in the .flake8 file)

#### Setup
Create a virtual env
Ensure the dependencies are met:
```
pip install poetry
poetry install
```

#### Run tests
The tests are run against a local network.  
Before running the tests you'll need to `docker-compose up` to create the local network, users and contracts used in the tests.  
When ready, just:
```
pytest
```



