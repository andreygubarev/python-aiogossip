# MODULE: aiogossip.types.endpoint

import ipaddress

import pytest

from aiogossip.types.address import Address
from aiogossip.types.endpoint import Endpoint


def test_endpoint_init_with_valid_addresses():
    saddr = Address(ipaddress.IPv4Address("192.168.1.1"), 8080)
    daddr = Address(ipaddress.IPv4Address("192.168.1.2"), 8080)
    endpoint = Endpoint(saddr, daddr)
    assert endpoint.saddr == saddr
    assert endpoint.daddr == daddr


def test_endpoint_init_with_none_addresses():
    endpoint = Endpoint(None, None)
    assert endpoint.saddr is None
    assert endpoint.daddr is None


def test_endpoint_init_with_invalid_saddr():
    daddr = Address(ipaddress.IPv4Address("192.168.1.2"), 8080)
    with pytest.raises(TypeError):
        Endpoint("invalid_address", daddr)


def test_endpoint_init_with_invalid_daddr():
    saddr = Address(ipaddress.IPv4Address("192.168.1.1"), 8080)
    with pytest.raises(TypeError):
        Endpoint(saddr, "invalid_address")
