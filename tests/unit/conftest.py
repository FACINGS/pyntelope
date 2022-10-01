import pytest

import pyntelope


@pytest.fixture(scope="module")
def net():
    net = pyntelope.Net(host="http://127.0.0.1:8888")
    yield net


@pytest.fixture
def auth():
    auth = pyntelope.Authorization(actor="user2", permission="active")
    yield auth
