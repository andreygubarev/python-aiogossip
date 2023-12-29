# MODULE: aiogossip.types.address

import dataclasses
import ipaddress

import pytest
import typeguard

from aiogossip.types.address import Address, to_address, to_ipaddress, to_port


def test_post_init_with_valid_ipv4_address_and_port():
    address = Address(ipaddress.IPv4Address("192.168.1.1"), 8080)
    assert isinstance(address.ip, ipaddress.IPv4Address)
    assert isinstance(address.port, int)


def test_post_init_with_valid_ipv6_address_and_port():
    address = Address(ipaddress.IPv6Address("2001:0db8:85a3:0000:0000:8a2e:0370:7334"), 8080)
    assert isinstance(address.ip, ipaddress.IPv6Address)
    assert isinstance(address.port, int)


def test_post_init_with_invalid_ip():
    with pytest.raises(TypeError):
        Address("invalid_ip", 8080)


def test_post_init_with_invalid_port():
    with pytest.raises(TypeError):
        Address(ipaddress.IPv4Address("192.168.1.1"), "invalid_port")


def test_post_init_with_invalid_port_integer():
    with pytest.raises(ValueError):
        Address(ipaddress.IPv4Address("192.168.1.1"), 70000)


def test_frozen_address():
    address = Address(ipaddress.IPv4Address("192.168.1.1"), 8080)
    with pytest.raises(dataclasses.FrozenInstanceError):
        address.ip = ipaddress.IPv4Address("127.0.0.1")


def test_address_slots():
    address = Address(ipaddress.IPv4Address("192.168.1.1"), 8080)
    with pytest.raises(AttributeError):
        address.invalid_attribute
    with pytest.raises(TypeError):
        address.invalid_attribute = "test"


def test_frozen_replacement():
    address = Address(ipaddress.IPv4Address("192.168.1.1"), 8080)
    address = dataclasses.replace(address, ip=ipaddress.IPv4Address("192.168.0.1"))
    assert address.ip == ipaddress.IPv4Address("192.168.0.1")


def test_to_ip_with_valid_ipv4_string():
    ip = to_ipaddress("192.168.1.1")
    assert isinstance(ip, ipaddress.IPv4Address)


def test_to_ip_with_valid_ipv6_string():
    ip = to_ipaddress("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
    assert isinstance(ip, ipaddress.IPv6Address)


def test_to_ip_with_valid_ipv4_object():
    ip = to_ipaddress(ipaddress.IPv4Address("192.168.1.1"))
    assert isinstance(ip, ipaddress.IPv4Address)


def test_to_ip_with_valid_ipv6_object():
    ip = to_ipaddress(ipaddress.IPv6Address("2001:0db8:85a3:0000:0000:8a2e:0370:7334"))
    assert isinstance(ip, ipaddress.IPv6Address)


def test_to_ip_with_invalid_ip_type():
    with pytest.raises(typeguard.TypeCheckError):
        to_ipaddress(123)


def test_to_ip_with_invalid_ip_format():
    with pytest.raises(ValueError):
        to_ipaddress("invalid_ip")


def test_to_ip_with_invalid_ipv4_address():
    with pytest.raises(ValueError):
        to_ipaddress("256.0.0.1")


def test_to_ip_with_invalid_ipv6_address():
    with pytest.raises(ValueError):
        to_ipaddress("2001:0db8:85a3:0000:0000:8a2e:0370:7334:1234")


def test_to_port_with_valid_integer():
    port = to_port(8080)
    assert isinstance(port, int)
    assert 0 <= port <= 65535


def test_to_port_with_valid_string():
    port = to_port("8080")
    assert isinstance(port, int)
    assert 0 <= port <= 65535


def test_to_port_with_valid_bytes():
    port = to_port(b"8080")
    assert isinstance(port, int)
    assert 0 <= port <= 65535


def test_to_port_with_valid_float():
    port = to_port(8080.0)
    assert isinstance(port, int)
    assert 0 <= port <= 65535


def test_to_port_with_invalid_string():
    with pytest.raises(ValueError):
        to_port("invalid_port")


def test_to_port_with_out_of_range_port():
    with pytest.raises(ValueError):
        to_port(70000)


def test_to_port_with_negative_port():
    with pytest.raises(ValueError):
        to_port(-1)


def test_to_port_with_non_numeric_string():
    with pytest.raises(ValueError):
        to_port("not_a_number")


def test_to_port_with_non_numeric_bytes():
    with pytest.raises(ValueError):
        to_port(b"not_a_number")


def test_to_port_with_invalid_type():
    with pytest.raises(typeguard.TypeCheckError):
        to_port([])


def test_to_address_with_valid_address_object():
    address = Address(ipaddress.IPv4Address("192.168.1.1"), 8080)
    result = to_address(address)
    assert isinstance(result, Address)
    assert result.ip == ipaddress.IPv4Address("192.168.1.1")
    assert result.port == 8080


def test_to_address_with_valid_string_address():
    result = to_address("192.168.1.1:8080")
    assert isinstance(result, Address)
    assert result.ip == ipaddress.IPv4Address("192.168.1.1")
    assert result.port == 8080


def test_to_address_with_valid_tuple_address():
    result = to_address(("192.168.1.1", 8080))
    assert isinstance(result, Address)
    assert result.ip == ipaddress.IPv4Address("192.168.1.1")
    assert result.port == 8080


def test_to_address_with_invalid_type():
    with pytest.raises(typeguard.TypeCheckError):
        to_address(123)


def test_to_address_with_invalid_string_format():
    with pytest.raises(ValueError):
        to_address("invalid_address")


def test_to_address_with_invalid_tuple_format():
    with pytest.raises(typeguard.TypeCheckError):
        to_address(("192.168.1.1", "invalid_port"))


def test_to_address_with_tuple_of_wrong_size():
    with pytest.raises(typeguard.TypeCheckError):
        to_address(("192.168.1.1", 8080, "extra_value"))


def test_address_str_representation():
    address = Address(ipaddress.IPv4Address("192.168.1.1"), 8080)
    assert str(address) == "192.168.1.1:8080"


def test_address_hash():
    address1 = Address(ipaddress.IPv4Address("192.168.1.1"), 8080)
    address2 = Address(ipaddress.IPv4Address("192.168.1.1"), 8080)
    assert hash(address1) == hash(address2)


def test_address_repr():
    address = Address(ipaddress.IPv4Address("192.168.1.1"), 8080)
    assert repr(address) == "<Address '192.168.1.1:8080'>"
