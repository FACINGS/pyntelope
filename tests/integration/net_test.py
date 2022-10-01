import re

import pytest

import pyntelope


aliases = [
    pyntelope.EosMainnet,
    pyntelope.KylinTestnet,
    pyntelope.Jungle3Testnet,
    pyntelope.TelosMainnet,
    pyntelope.TelosTestnet,
    pyntelope.ProtonMainnet,
    pyntelope.ProtonTestnet,
    pyntelope.UosMainnet,
    pyntelope.FioMainnet,
    pyntelope.WaxTestnet,
    pyntelope.WaxMainnet,
]


@pytest.mark.flaky(reruns=3)
@pytest.mark.parametrize("alias", aliases)
def test_get_info_from_alias(alias):
    net = alias()
    info = net.get_info()
    assert isinstance(info, dict)
    assert "chain_id" in info
    patt = r"[a-f0-9]{64}"
    assert re.fullmatch(patt, info["chain_id"])
