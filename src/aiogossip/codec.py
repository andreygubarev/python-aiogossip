import dataclasses
import ipaddress
import uuid

import msgpack

from . import address, endpoint, message, node


def dataclass_asdict(dataclass):
    """
    Convert a dataclass object to a dictionary without recursive conversion.

    Args:
        dataclass: The dataclass object to convert.

    Returns:
        dict: A dictionary representation of the dataclass object.
    """
    return {f.name: getattr(dataclass, f.name) for f in dataclasses.fields(dataclass)}


def dataclass_astuple(dataclass):
    """
    Convert a dataclass instance to a tuple without recursive conversion.

    Args:
        dataclass: The dataclass instance to convert.

    Returns:
        tuple: The converted tuple.
    """
    return tuple(getattr(dataclass, f.name) for f in dataclasses.fields(dataclass))


def encoder(obj):
    if isinstance(obj, set):
        return msgpack.ExtType(0, packb(list(obj)))
    if isinstance(obj, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
        return msgpack.ExtType(1, bytes(obj.packed))
    if isinstance(obj, uuid.UUID):
        return msgpack.ExtType(2, bytes(obj.bytes))
    if isinstance(obj, address.Address):
        return msgpack.ExtType(3, packb(dataclass_astuple(obj)))
    if isinstance(obj, node.Node):
        return msgpack.ExtType(4, packb(dataclass_astuple(obj)))
    if isinstance(obj, endpoint.Endpoint):
        return msgpack.ExtType(5, packb(dataclass_astuple(obj)))
    if isinstance(obj, message.Message):
        return msgpack.ExtType(6, packb(dataclass_asdict(obj)))
    if isinstance(obj, message.Message.Type):
        return msgpack.ExtType(7, packb(obj.value))
    raise TypeError(f"Object of type {type(obj)} is not serializable")  # pragma: no cover


def decoder(code, data):
    if code == 0:
        return set(unpackb(data))
    if code == 1:
        return ipaddress.ip_address(data)
    if code == 2:
        return uuid.UUID(bytes=data)
    if code == 3:
        return address.Address(*unpackb(data))
    if code == 4:
        return node.Node(*unpackb(data))
    if code == 5:
        return endpoint.Endpoint(*unpackb(data))
    if code == 6:
        return message.Message(**unpackb(data))
    if code == 7:
        return message.Message.Type(unpackb(data))
    return msgpack.ExtType(code, data)  # pragma: no cover


def packb(message):
    return msgpack.packb(message, default=encoder, use_bin_type=False)


def unpackb(message):
    return msgpack.unpackb(message, ext_hook=decoder)
